import asyncio
import logging
from asyncio import AbstractEventLoop
from typing import Any, AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from settings import get_test_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.types import String, TypeDecorator
from test_models.base import TestBase

from src.app import create_application

pytest_plugins = ["pytest_asyncio"]
settings = get_test_settings()


class PostgresEnum(TypeDecorator[str]):
    """Custom type decorator for handling PostgreSQL enums in SQLite."""
    
    impl = String
    cache_ok = True  # Wymagane dla nowszych wersji SQLAlchemy

    def __init__(self, enum_type: Any) -> None:
        super().__init__()
        self.enum_type = enum_type


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create test application instance."""
    return create_application()


@pytest.fixture(scope="session")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create async test database engine."""
    engine = create_async_engine(
        get_test_settings().ASYNC_DATABASE_URI,
        echo=False,
        connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
        await conn.run_sync(TestBase.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session = async_sessionmaker(
        test_db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def auth_token(async_client: AsyncClient) -> str:
    """Get authentication token for testing."""
    response = await async_client.post(
        "/auth/login",
        data={
            "username": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict[str, str]:
    """Get authentication headers for testing."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=True)
async def clean_database(db_session: AsyncSession) -> None:
    """Clean database between tests."""
    try:
        for table in reversed(TestBase.metadata.sorted_tables):
            await db_session.execute(text(f"DELETE FROM {table.name}"))
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        print(f"Error cleaning database: {e}")


@pytest.fixture(scope="function")
async def prepare_database(db_session: AsyncSession) -> None:
    """Prepare database for testing."""
    try:
        # Wyczyść wszystkie tabele
        for table in reversed(TestBase.metadata.sorted_tables):
            await db_session.execute(text(f"DELETE FROM {table.name}"))
        
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        logging.error(f"Error in prepare_database: {e}")
        raise


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """Create an instance of the asyncio event loop."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()