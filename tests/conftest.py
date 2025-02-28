import logging
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

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
from sqlalchemy.types import String, TypeDecorator
from test_models.models_db_test import TestBase, TestUser
from werkzeug.security import generate_password_hash

from src.app import create_application
from src.token_storage import TokenStorage

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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
async def create_test_user(db_session: AsyncSession) -> AsyncGenerator[TestUser, None]:
    """Create a test user in the database."""
    password = "Test123!"
    hashed_password = generate_password_hash(password)
    
    # Używamy tego samego ciągu znaków dla user_name i email
    # dzięki czemu logowanie zadziała niezależnie od tego, które pole jest używane
    test_identifier = "test@example.com"
    
    user = TestUser(
        user_name=test_identifier,  # Ten sam identyfikator
        email=test_identifier,      # Ten sam identyfikator
        hash=hashed_password
    )
    
    logging.info(f"Creating test user: {user.user_name}, email: {user.email}")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Sprawdź, czy użytkownik został poprawnie zapisany
    verification_query = await db_session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": test_identifier}
    )
    result = verification_query.fetchone()
    logging.info(f"Verification query result: {result}")
    
    yield user
    
    logging.info(f"Deleting test user: {user.user_name}")
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def auth_token(async_client: AsyncClient, create_test_user: TestUser) -> str:
    """Get authentication token for testing."""
    # Używamy oryginalnego hasła, a nie hasha
    response = await async_client.post(
        "/auth/login",
        data={
            "username": create_test_user.email,
            "password": "Test123!"  # Używamy oryginalnego hasła, nie hasha
        }
    )
    
    if response.status_code != 200:
        logging.error(f"Auth failed: {response.status_code} - {response.text}")
        
    assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict[str, str]:
    """Get authentication headers for testing."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=True)
async def clean_database(db_session: AsyncSession) -> None:
    """Clean database between tests."""
    logging.info("Cleaning database before test")
    try:
        for table in reversed(TestBase.metadata.sorted_tables):
            await db_session.execute(text(f"DELETE FROM {table.name}"))
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        logging.error(f"Error cleaning database: {e}")


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


@pytest.fixture
async def mock_db_session() -> AsyncGenerator[AsyncMock, None]:
    """Fixture dostarczająca mock dla sesji bazy danych."""
    db_mock = AsyncMock(spec=AsyncSession)
    
    # Możesz dodać więcej mockowania, jeśli to konieczne
    yield db_mock


@pytest.fixture(scope="session", autouse=True)
def patch_redis() -> Generator[None, None, None]:
    """Mockuj Redis na poziomie modułu dla wszystkich testów."""
    # Tworzymy mock Redis
    mock_redis = AsyncMock(spec=Redis)
    mock_redis.ping.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.exists.return_value = 1
    mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
    mock_redis.__aexit__ = AsyncMock(return_value=None)
    mock_redis.aclose = AsyncMock(return_value=None)
    
    # Mockujemy klasę Redis i jej metody
    with patch("redis.asyncio.Redis", return_value=mock_redis), \
         patch("redis.asyncio.Redis.from_url", return_value=mock_redis), \
         patch("src.dependencies.Redis", return_value=mock_redis):
        
        # Mockujemy funkcję get_redis
        async def mock_get_redis() -> AsyncGenerator[Redis, None]:
            yield mock_redis
            
        with patch("src.dependencies.get_redis", mock_get_redis):
            yield


@pytest.fixture(scope="function")
def mock_token_storage() -> AsyncMock:
    """Fixture dostarczająca mock dla TokenStorage."""
    mock = AsyncMock(spec=TokenStorage)
    mock.store.return_value = None
    mock.exists.return_value = False
    return mock


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Fixture dostarczająca mock dla Redis."""
    mock = AsyncMock(spec=Redis)
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.exists.return_value = 1
    return mock


@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new async session for testing with SQLite."""
    settings = get_test_settings()
    engine = create_async_engine(settings.ASYNC_DATABASE_URI, echo=True)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
        await conn.run_sync(TestBase.metadata.create_all)

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    await engine.dispose()