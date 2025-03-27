import logging
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from settings import get_test_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from test_models.models_db_test import TestBase, TestUser
from werkzeug.security import generate_password_hash

from src.app import create_application

pytest_plugins = ["pytest_asyncio"]
settings = get_test_settings()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db() -> Generator[None, None, None]:
    db_url = settings.ASYNC_DATABASE_URI
    if db_url.startswith("sqlite:///"):
        file_path = db_url[len("sqlite:///"):]
    elif db_url.startswith("sqlite+aiosqlite:///"):
        file_path = db_url[len("sqlite+aiosqlite:///"):]
    else:
        file_path = None 

    if file_path:
        logging.info(f"Checking for database file: {file_path}")
        if os.path.exists(file_path):
            logging.info(f"Deleting test database file: {file_path}")
            os.remove(file_path)
            logging.info(f"Test database file '{file_path}' deleted.")
        else:
            logging.info(f"Test database file '{file_path}' not found, skipping deletion.")
    else:
        logging.info("Database cleanup not applicable for non-file-based databases.")
    yield


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return create_application()


@pytest.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URI,
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


@pytest.fixture(scope="function")
async def create_test_user(db_session: AsyncSession) -> AsyncGenerator[TestUser, None]:
    password = settings.TEST_USER_PASSWORD
    hashed_password = generate_password_hash(password)
    
    test_email = settings.TEST_USER_EMAIL
    test_user_name = settings.TEST_USER_NAME
    
    user = TestUser(
        user_name=test_user_name,
        email=test_email,
        hash=hashed_password
    )
    
    logging.info(f"Creating test user: {user.user_name}, email: {user.email}")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    verification_query = await db_session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": test_email}
    )
    result = verification_query.fetchone()
    logging.info(f"Verification query result: {result}")
    
    yield user
    
    logging.info(f"Deleting test user: {user.user_name}")
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture(scope="function")
async def auth_token(async_client: AsyncClient, create_test_user: TestUser) -> str:
    response = await async_client.post(
        "/auth/login",
        data={
            "username": create_test_user.user_name,
            "password": settings.TEST_USER_PASSWORD
        }
    )

    if response.status_code != 200:
        logging.error(f"Auth failed: {response.status_code} - {response.text}")

    assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def mock_redis() -> AsyncMock:
    mock = AsyncMock(spec=Redis)
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.exists.return_value = 1
    mock.delete.return_value = 1
    return mock
