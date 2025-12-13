"""
Database Configuration - Async SQLAlchemy with Connection Pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import settings

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

# Base class for models
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
