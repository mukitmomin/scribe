"""
Database configuration with async SQLAlchemy and PostgreSQL.

This module provides the async engine, session factory, and database dependency
for FastAPI endpoints.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# Use NullPool for async to avoid connection conflicts
# This is important for compatibility with sync test clients
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool,  # Prevents "operation in progress" errors
)

# Use async_sessionmaker (the modern way) instead of sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    """
    Dependency that provides a database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
