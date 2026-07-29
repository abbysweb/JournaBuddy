"""
JournaBuddy Database Session Factory
Provides async SQLAlchemy engine and session dependency for FastAPI endpoints.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Async engine connected to PostgreSQL
engine = create_async_engine(
    settings.database_url,
    echo=False,           # Set True for SQL query logging
    pool_pre_ping=True,   # Automatically reconnect on stale connections
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async DB session per request.
    Automatically closes the session after the request is handled.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
