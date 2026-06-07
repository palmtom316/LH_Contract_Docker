"""
Database Configuration - Async SQLAlchemy with Connection Pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import inspect, text

from app.config import settings

REQUIRED_SCHEMA_TABLES = (
    "users",
    "contracts_upstream",
    "contracts_downstream",
    "contracts_management",
    "expenses_non_contract",
    "sys_dictionaries",
    "sys_config",
    "refresh_tokens",
)

# Create async engine with connection pooling
# QueuePool is recommended for production environments
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Use connection pool for better performance in production
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,           # Number of connections to keep open
    max_overflow=10,       # Additional connections allowed beyond pool_size
    pool_timeout=30,       # Seconds to wait for a connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Test connection validity before use
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Backward-compatible export for legacy Feishu integrations.
async_session = AsyncSessionLocal

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Verify database connectivity and required schema without mutating it."""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        await verify_required_schema(conn)


async def verify_required_schema(executor):
    """Fail fast when migrations have not created the required tables."""
    def read_table_names(sync_obj):
        bind = getattr(sync_obj, "bind", sync_obj)
        return set(inspect(bind).get_table_names())

    table_names = await executor.run_sync(read_table_names)
    missing_tables = [
        table_name for table_name in REQUIRED_SCHEMA_TABLES
        if table_name not in table_names
    ]

    if missing_tables:
        joined = ", ".join(missing_tables)
        raise RuntimeError(
            f"Database schema is incomplete; run `alembic upgrade head`. Missing tables: {joined}"
        )


async def close_db():
    """Close database connection and dispose connection pool"""
    await engine.dispose()
