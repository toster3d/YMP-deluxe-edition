from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# from redis.asyncio import Redis
from settings import get_test_settings
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel

# from extensions import Base
from src.app import app as fastapi_app

settings = get_test_settings()

@pytest.fixture(scope="session")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URI,
        echo=settings.DEBUG,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with AsyncSession(test_db_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI test application."""
    return fastapi_app

@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Get authentication headers."""
    response = await client.post(
        "/auth/login",
        json={
            "email": settings.TEST_USER_EMAIL,
            "password": settings.TEST_USER_PASSWORD
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}