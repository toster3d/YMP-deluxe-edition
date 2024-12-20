from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings
from token_storage import logger

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Konfiguracja silnika bazy danych z parametrami odpowiednimi dla SQLite
async_engine: AsyncEngine = create_async_engine(
    url=settings.async_database_uri,
    echo=settings.debug,
    # Optymalne ustawienia dla SQLite
    pool_pre_ping=True,  # Sprawdza połączenie przed użyciem
    # Ustawienia specyficzne dla SQLite
    connect_args={
        "check_same_thread": False,
        "timeout": 30,    # Timeout połączenia w sekundach
    }
)

# Konfiguracja sesji
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session context manager.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        HTTPException: If database operation fails
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
    finally:
        await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency dla FastAPI
DbSession = AsyncSession


async def test_database_connection() -> None:
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise
