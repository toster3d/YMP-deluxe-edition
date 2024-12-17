from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


# Create async engine with simplified configuration
async_engine: AsyncEngine = create_async_engine(
    url=settings.async_database_uri,
    echo=settings.debug,
    pool_size=5,  # Zmniejszona pula połączeń
    max_overflow=5,  # Zmniejszony maksymalny overflow
    future=True,
    pool_pre_ping=True,  # Sprawdzanie połączenia przed użyciem
    pool_recycle=1800  # Recykling połączeń co 30 minut
)

# Configure async session maker with basic settings
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    future=True
)


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session context manager.
    
    Yields:
        AsyncSession: Database session that will be automatically closed
        
    Raises:
        HTTPException: If database operation fails
        
    Example:
        ```python
        async with get_async_db_context() as session:
            result = await session.execute(query)
            await session.commit()
        ```
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) from e
    finally:
        await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency.
    
    Yields:
        AsyncSession: Database session that will be automatically closed
        
    Raises:
        HTTPException: If database operation fails
        
    Example:
        ```python
        @router.get("/items")
        async def get_items(db: DbSession):
            result = await db.execute(query)
            return result
        ```
    """
    async with get_async_db_context() as session:
        yield session


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_async_db)]

