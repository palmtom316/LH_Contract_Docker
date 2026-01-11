"""
Enhanced Database Configuration with Environment-based Pool Settings
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
import os

from app.config import settings

# Environment-based pool configuration
ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV == "production"

# Dynamic pool sizing based on environment
POOL_CONFIG = {
    "development": {"pool_size": 5, "max_overflow": 10},
    "production": {"pool_size": 20, "max_overflow": 40},
    "test": {"pool_size": 2, "max_overflow": 5}
}

config = POOL_CONFIG.get(ENV, POOL_CONFIG["development"])

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=config["pool_size"],
    max_overflow=config["max_overflow"],
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo_pool=settings.DEBUG,  # Log pool events in debug mode
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection and dispose connection pool"""
    await engine.dispose()
