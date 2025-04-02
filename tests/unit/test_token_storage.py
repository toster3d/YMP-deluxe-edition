from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis

from config import get_settings
from src.token_storage import RedisTokenStorage


class TestRedisConnection:
    """Test basic Redis connection and ping."""

    @pytest.mark.asyncio
    async def test_redis_connection(self, mock_redis: AsyncMock) -> None:
        """Test basic Redis connection using ping."""
        mock_redis.ping = AsyncMock(return_value=True)
        result = await mock_redis.ping()
        assert result is True


class TestTokenStorageOperations:
    """Test token storage and retrieval operations."""

    @pytest.fixture
    def mock_redis_client(self) -> MagicMock:
        """Fixture for mock Redis client."""
        mock = MagicMock(spec=Redis)
        mock.setex = AsyncMock()
        mock.exists = AsyncMock(return_value=1)
        return mock

    @pytest.fixture
    def token_storage(self, mock_redis_client: MagicMock) -> RedisTokenStorage:
        """Fixture for RedisTokenStorage with mock client."""
        return RedisTokenStorage(mock_redis_client)

    @pytest.mark.asyncio
    async def test_store_and_check_token(self, token_storage: RedisTokenStorage, mock_redis_client: MagicMock) -> None:
        """Test storing and checking a token."""
        token = "test_token"
        expires_delta = timedelta(minutes=30)
        settings = get_settings()

        await token_storage.store(token, expires_delta)
        exists = await token_storage.exists(token)

        assert exists is True
        expected_key = f"{settings.redis_prefix}{token}"
        mock_redis_client.setex.assert_called_once()
        mock_redis_client.exists.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_check_nonexistent_token(self, token_storage: RedisTokenStorage, mock_redis_client: MagicMock) -> None:
        """Test checking a token that doesn't exist."""
        mock_redis_client.exists.return_value = 0
        token = "nonexistent_token"
        settings = get_settings()

        exists = await token_storage.exists(token)

        assert exists is False
        expected_key = f"{settings.redis_prefix}{token}"
        mock_redis_client.exists.assert_called_once_with(expected_key)


class TestTokenBlacklist:
    """Test token blacklisting functionality."""

    @pytest.fixture
    def mock_redis_client(self) -> MagicMock:
        """Fixture for mock Redis client."""
        mock = MagicMock(spec=Redis)
        mock.setex = AsyncMock()
        mock.exists = AsyncMock()
        return mock

    @pytest.fixture
    def token_storage(self, mock_redis_client: MagicMock) -> RedisTokenStorage:
        """Fixture for RedisTokenStorage with mock client."""
        return RedisTokenStorage(mock_redis_client)

    @pytest.mark.asyncio
    async def test_token_blacklist(self, token_storage: RedisTokenStorage, mock_redis_client: MagicMock) -> None:
        """Test adding a token to the blacklist."""
        mock_redis_client.exists.return_value = 1
        token = "blacklisted_token"
        expiration = timedelta(minutes=60)

        await token_storage.store(token, expiration)
        is_blacklisted = await token_storage.exists(token)

        assert is_blacklisted is True

    @pytest.mark.asyncio
    async def test_token_expiration(self, token_storage: RedisTokenStorage, mock_redis_client: MagicMock) -> None:
        """Test checking a token after it has expired."""
        mock_redis_client.exists.return_value = 0
        token = "expired_token"
        expiration = timedelta(seconds=1)

        await token_storage.store(token, expiration)
        is_blacklisted = await token_storage.exists(token)

        assert is_blacklisted is False


class TestJTITokenStorage:
    """Test storage and checking of JTI tokens."""

    @pytest.fixture
    def mock_redis_client(self) -> AsyncMock:
        """Fixture for mock Redis client (AsyncMock)."""
        mock = AsyncMock(spec=Redis)
        mock.setex = AsyncMock()
        mock.exists = AsyncMock()
        return mock

    @pytest.fixture
    def token_storage(self, mock_redis_client: AsyncMock) -> RedisTokenStorage:
        """Fixture for RedisTokenStorage with mock client."""
        return RedisTokenStorage(mock_redis_client)

    @pytest.mark.asyncio
    async def test_store_jti_token(self, token_storage: RedisTokenStorage, mock_redis_client: AsyncMock) -> None:
        """Test storing a JTI token."""
        jti = "test-jti"
        expires_in = timedelta(hours=1)

        mock_redis_client.setex.reset_mock()  # Reset mock before asserting call

        await token_storage.store(jti, expires_in)

        mock_redis_client.setex.assert_called_once()
        args, _ = mock_redis_client.setex.call_args
        assert args[0] == f"{token_storage.settings.redis_prefix}{jti}"
        assert args[1] == int(expires_in.total_seconds())
        assert args[2] == token_storage.settings.redis_blacklist_value

    @pytest.mark.asyncio
    async def test_check_jti_token_exists(self, token_storage: RedisTokenStorage, mock_redis_client: AsyncMock) -> None:
        """Test checking if a JTI token exists."""
        jti = "test-jti-exists"

        mock_redis_client.exists.return_value = 1
        result = await token_storage.exists(jti)
        assert result is True
        mock_redis_client.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")

        mock_redis_client.exists.return_value = 0
        result = await token_storage.exists(jti)
        assert result is False
        mock_redis_client.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")


class TestJWTTokenStorage:
    """Test storage and checking of JWT tokens."""

    @pytest.fixture
    def mock_redis_client(self) -> MagicMock:
        """Fixture for mock Redis client."""
        mock = MagicMock(spec=Redis)
        mock.setex = AsyncMock()
        mock.exists = AsyncMock(return_value=1)
        return mock

    @pytest.fixture
    def token_storage(self, mock_redis_client: MagicMock) -> RedisTokenStorage:
        """Fixture for RedisTokenStorage with mock client."""
        return RedisTokenStorage(mock_redis_client)

    @pytest.mark.asyncio
    async def test_jwt_token_storage(self, token_storage: RedisTokenStorage, mock_redis_client: MagicMock) -> None:
        """Test storing and checking a JWT token."""
        token = "test_jwt_token"
        expires_delta = timedelta(minutes=30)

        await token_storage.store(token, expires_delta)
        exists = await token_storage.exists(token)

        assert exists is True
        mock_redis_client.setex.assert_called_once()
        mock_redis_client.exists.assert_called_once_with(f"{token_storage.settings.redis_prefix}{token}") 