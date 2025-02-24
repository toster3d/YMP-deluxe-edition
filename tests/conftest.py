import logging
import uuid
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from settings import get_test_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlmodel import SQLModel
from test_models.models_db_test import TestUser, TestBase
from sqlalchemy.pool import StaticPool

from src.app import create_application

pytest_plugins = ["pytest_asyncio"]
settings = get_test_settings()

@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Tworzy instancję aplikacji testowej."""
    return create_application()

@pytest.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Tworzy asynchronicznego klienta do testowania."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    """Create engine once per session."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.TEST_DB_ECHO,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    return engine

@pytest.fixture(autouse=True)
async def setup_database(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Setup database before tests."""
    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    async_session = async_sessionmaker(
        engine, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def unique_user(db_session: AsyncSession) -> TestUser:
    """Fixture tworząca unikalnego użytkownika."""
    user = TestUser(
        user_name=f"TestUser-{uuid.uuid4()}",
        hash="hashedpassword",
        email=f"test{uuid.uuid4()}@example.com"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_token(async_client: AsyncClient) -> str:
    """Pobiera token autoryzacyjny dla testów."""
    response = await async_client.post(
        "/auth/login",
        data={"username": settings.TEST_USER_EMAIL, "password": settings.TEST_USER_PASSWORD}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
async def auth_headers(auth_token: str) -> dict[str, str]:
    """Tworzy nagłówki autoryzacyjne do testowania."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(autouse=True)
async def clean_database(db_session: AsyncSession) -> None:
    """Czyści bazę danych między testami."""
    try:
        await db_session.execute(text("PRAGMA foreign_keys = OFF"))
        for table in reversed(SQLModel.metadata.sorted_tables):
            await db_session.execute(text(f"DELETE FROM {table.name}"))
        await db_session.execute(text("PRAGMA foreign_keys = ON"))
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        logging.error(f"Błąd czyszczenia bazy danych: {e}")
        raise
