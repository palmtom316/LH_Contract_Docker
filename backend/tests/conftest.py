"""
Pytest Configuration and Fixtures
Provides common test fixtures and configuration for all tests
"""
import pytest
import asyncio
import inspect
import os
import re
import asyncpg
import socket
from typing import Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import make_url

from app.main import app
from app.database import get_db, Base
from app.models.user import User, UserRole
from app.services.auth import get_password_hash, create_access_token
from app.core.rate_limit import limiter


# Test database URL (isolated PostgreSQL database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://lh_admin:dev_password_change_me@127.0.0.1:5432/lh_contract_test_db",
)


def pytest_pycollect_makeitem(collector, name, obj):
    """
    Avoid collecting helper classes imported from external libraries as tests.
    """
    if inspect.isclass(obj) and name.startswith("Test") and obj.__module__.startswith("_pytest."):
        return []
    return None


def pytest_pyfunc_call(pyfuncitem):
    """
    Minimal async test runner for environments without pytest-asyncio.
    """
    test_func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_func):
        return None

    loop = pyfuncitem.funcargs.get("event_loop")
    created_loop = False
    if loop is None:
        loop = asyncio.new_event_loop()
        created_loop = True

    kwargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
    try:
        loop.run_until_complete(test_func(**kwargs))
    finally:
        if created_loop:
            loop.close()
    return True


def _run(loop, coro):
    return loop.run_until_complete(coro)


async def _ensure_postgres_test_database():
    test_url = make_url(TEST_DATABASE_URL)
    db_name = test_url.database
    if not db_name:
        raise RuntimeError("TEST_DATABASE_URL missing database name")
    if not re.match(r"^[A-Za-z0-9_]+$", db_name):
        raise RuntimeError(f"Unsafe test database name: {db_name}")

    admin_url = test_url.set(database="postgres")
    conn = await asyncpg.connect(
        user=admin_url.username,
        password=admin_url.password,
        host=admin_url.host,
        port=admin_url.port or 5432,
        database=admin_url.database,
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


def _database_unavailable_message(exc: Exception) -> str:
    if isinstance(exc, PermissionError):
        return f"PostgreSQL test database unavailable: permission denied ({exc})"
    if isinstance(exc, (asyncpg.PostgresError, OSError, socket.error)):
        return f"PostgreSQL test database unavailable: {exc}"
    return f"PostgreSQL test database unavailable: {type(exc).__name__}: {exc}"


def _ensure_postgres_test_database_or_skip(event_loop) -> None:
    try:
        _run(event_loop, _ensure_postgres_test_database())
    except pytest.skip.Exception:
        raise
    except Exception as exc:
        pytest.skip(_database_unavailable_message(exc))


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db(event_loop) -> Generator[AsyncSession, None, None]:
    """
    Create a test database session
    Each test gets a fresh database
    """
    _ensure_postgres_test_database_or_skip(event_loop)
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    async def _reset_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    _run(event_loop, _reset_tables())

    TestSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    session = TestSessionLocal()
    try:
        yield session
    finally:
        _run(event_loop, session.close())

        async def _cleanup_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

        _run(event_loop, _cleanup_tables())
        _run(event_loop, engine.dispose())


@pytest.fixture
def client(event_loop, test_db: AsyncSession):
    """
    Create test HTTP client
    Uses test database instead of production database
    """
    storage = getattr(limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()

    # Override database dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db

    client_cm = AsyncClient(app=app, base_url="http://test")
    ac = _run(event_loop, client_cm.__aenter__())
    try:
        yield ac
    finally:
        _run(event_loop, client_cm.__aexit__(None, None, None))
        app.dependency_overrides.clear()
        if storage and hasattr(storage, "reset"):
            storage.reset()


@pytest.fixture
def test_user(event_loop, test_db: AsyncSession) -> User:
    """Create a test user"""
    async def _create():
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            role=UserRole.BIDDING,  # Changed from VIEWER (deprecated) to BIDDING
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    return _run(event_loop, _create())


@pytest.fixture
def test_admin(event_loop, test_db: AsyncSession) -> User:
    """Create a test admin user"""
    async def _create():
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True
        )
        test_db.add(admin)
        await test_db.commit()
        await test_db.refresh(admin)
        return admin

    return _run(event_loop, _create())


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Get admin authentication token"""
    token_data = {"sub": str(test_admin.id), "username": test_admin.username, "role": test_admin.role.value}
    return create_access_token(token_data)


@pytest.fixture
def user_token(test_user: User) -> str:
    """Get user authentication token"""
    token_data = {"sub": str(test_user.id), "username": test_user.username, "role": test_user.role.value}
    return create_access_token(token_data)


@pytest.fixture
def general_affairs_user(event_loop, test_db: AsyncSession) -> User:
    """Create a general affairs user"""
    async def _create():
        user = User(
            username="general_affairs",
            email="general@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="General Affairs",
            role=UserRole.GENERAL_AFFAIRS,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    return _run(event_loop, _create())


@pytest.fixture
def general_affairs_token(general_affairs_user: User) -> str:
    """Get general affairs authentication token"""
    token_data = {
        "sub": str(general_affairs_user.id),
        "username": general_affairs_user.username,
        "role": general_affairs_user.role.value
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    """Get authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}
