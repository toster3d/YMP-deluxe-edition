from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

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


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session dependency.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        HTTPException: If database operation fails
    """
    async with async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )


# Dependency dla FastAPI
DbSession = AsyncSession
