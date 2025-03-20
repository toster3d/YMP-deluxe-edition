import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from config import get_settings
from src.token_storage import RedisTokenStorage, TokenStorage, TokenStorageError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_redis_connection(mock_redis: AsyncMock) -> None:
    """Test basic Redis connection."""
    mock_redis.ping = AsyncMock(return_value=True)
    result = await mock_redis.ping()
    assert result is True

@pytest.mark.asyncio
async def test_store_and_check_token() -> None:
    """Test storing and checking token in Redis."""
    mock_redis = MagicMock()
    
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.exists.return_value = 1  # Redis.exists returns int (1 = True)
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_token"
    expires_delta = timedelta(minutes=30)
    settings = get_settings()
    
    await token_storage.store(token, expires_delta)
    exists = await token_storage.exists(token)
    
    logger.debug(f"mock_redis.exists.call_count: {mock_redis.exists.call_count}")
    logger.debug(f"mock_redis.exists.call_args: {mock_redis.exists.call_args}")
    logger.debug(f"exists result: {exists}")
    
    assert exists is True, f"Expected exists to be True, got {exists}"
    
    expected_key = f"{settings.redis_prefix}{token}"
    mock_redis.setex.assert_called_once()
    mock_redis.exists.assert_called_once_with(expected_key)

@pytest.mark.asyncio
async def test_check_nonexistent_token() -> None:
    """Test checking a token that doesn't exist."""
    mock_redis = MagicMock()
    mock_redis.exists = AsyncMock()
    mock_redis.exists.return_value = 0  # Token does not exist
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "nonexistent_token"
    settings = get_settings()
    
    exists = await token_storage.exists(token)
    
    assert exists is False
    
    expected_key = f"{settings.redis_prefix}{token}"
    mock_redis.exists.assert_called_once_with(expected_key)

@pytest.mark.asyncio
async def test_token_blacklist() -> None:
    """Test adding token to blacklist."""
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration = timedelta(minutes=60)
    
    mock_redis = MagicMock(spec=Redis)
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # Important: set return_value=1
    
    token_storage = RedisTokenStorage(mock_redis)
    
    await token_storage.store(token, expiration)
    
    is_blacklisted = await token_storage.exists(token)
    assert is_blacklisted is True

@pytest.mark.asyncio
async def test_token_expiration() -> None:
    """Test token expiration."""
    token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration: timedelta = timedelta(seconds=1)
    
    mock_redis = MagicMock(spec=Redis)
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)  # Token does not exist (expired)
    
    token_storage = RedisTokenStorage(mock_redis)
    
    await token_storage.store(token, expiration)
    
    is_blacklisted = await token_storage.exists(token)
    assert is_blacklisted is False

@pytest.mark.asyncio
async def test_store_jti_token(mock_redis: AsyncMock) -> None:
    """Test adding JTI token to blacklist."""
    token_storage = RedisTokenStorage(mock_redis)
    jti = "test-jti"
    expires_in = timedelta(hours=1)
    
    mock_redis.setex.reset_mock()
    mock_redis.setex = AsyncMock()
    
    await token_storage.store(jti, expires_in)
    
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0] == f"{token_storage.settings.redis_prefix}{jti}"
    assert args[1] == int(expires_in.total_seconds())
    assert args[2] == token_storage.settings.redis_blacklist_value

@pytest.mark.asyncio
async def test_check_jti_token_exists(mock_redis: AsyncMock) -> None:
    """Test checking if JTI token is in blacklist."""
    token_storage = RedisTokenStorage(mock_redis)
    jti = "test-jti"
    
    mock_redis.exists = AsyncMock(return_value=1)
    
    result = await token_storage.exists(jti)
    assert result is True
    mock_redis.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")
    
    mock_redis.exists = AsyncMock(return_value=0)
    
    result = await token_storage.exists(jti)
    assert result is False
    mock_redis.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")

@pytest.mark.asyncio
async def test_jwt_token_storage() -> None:
    """Test adding and checking JWT token in Redis."""
    mock_redis = MagicMock()
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # Simulate that token exists
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_jwt_token"
    expires_delta = timedelta(minutes=30)
    
    await token_storage.store(token, expires_delta)
    exists = await token_storage.exists(token)
    
    assert exists is True
    mock_redis.setex.assert_called_once()
    mock_redis.exists.assert_called_once_with(f"{token_storage.settings.redis_prefix}{token}")

@pytest.mark.asyncio
async def test_token_storage_abstract_methods() -> None:
    """Test that TokenStorage abstract methods raise NotImplementedError when not implemented."""
    class IncompleteTokenStorage(TokenStorage):
        pass
    
    with pytest.raises(TypeError) as exc_info:
        IncompleteTokenStorage()  # type: ignore
    
    assert "Can't instantiate abstract class" in str(exc_info.value)
    assert "store" in str(exc_info.value)
    assert "exists" in str(exc_info.value)
    
    class PartialTokenStorage(TokenStorage):
        async def store(self, token: str, expires_delta: timedelta) -> None:
            pass
    
    with pytest.raises(TypeError) as exc_info:
        PartialTokenStorage() # type: ignore
    
    assert "Can't instantiate abstract class" in str(exc_info.value)
    assert "exists" in str(exc_info.value)
    
    class MinimalTokenStorage(TokenStorage):
        async def store(self, token: str, expires_delta: timedelta) -> None:
            pass
        
        async def exists(self, token: str) -> bool:
            return False
    
    storage = MinimalTokenStorage()
    assert isinstance(storage, TokenStorage)

@pytest.mark.asyncio
async def test_redis_token_storage_error_handling_store() -> None:
    """Test error handling in RedisTokenStorage.store method."""
    mock_redis = MagicMock()
    mock_redis.setex = AsyncMock(side_effect=ConnectionError("Connection refused"))
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_token"
    expires_delta = timedelta(minutes=30)
    
    with pytest.raises(TokenStorageError) as exc_info:
        await token_storage.store(token, expires_delta)
    
    assert "Failed to store token" in str(exc_info.value)
    assert "Connection refused" in str(exc_info.value)

@pytest.mark.asyncio
async def test_redis_token_storage_error_handling_exists() -> None:
    """Test error handling in RedisTokenStorage.exists method."""
    mock_redis = MagicMock()
    mock_redis.exists = AsyncMock(side_effect=TimeoutError("Operation timed out"))
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_token"
    
    with pytest.raises(TokenStorageError) as exc_info:
        await token_storage.exists(token)
    
    assert "Failed to check token" in str(exc_info.value)
    assert "Operation timed out" in str(exc_info.value)

@pytest.mark.asyncio
async def test_redis_token_storage_cleanup() -> None:
    """Test cleanup method in RedisTokenStorage."""
    mock_redis = MagicMock()
    
    class AsyncIterMock:
        def __init__(self, items: list[str]) -> None:
            self.items = items.copy()  # Use copy() to avoid modifying the original list
            
        def __aiter__(self) -> "AsyncIterMock":
            return self
            
        async def __anext__(self) -> str:
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)
    
    mock_redis.scan_iter = lambda pattern: AsyncIterMock(["prefix:token1", "prefix:token2"])
    mock_redis.delete = AsyncMock()
    
    token_storage = RedisTokenStorage(mock_redis)
    
    await token_storage.cleanup()
    
    mock_redis.delete.assert_called_once_with("prefix:token1", "prefix:token2")

@pytest.mark.asyncio
async def test_redis_token_storage_cleanup_no_keys() -> None:
    """Test cleanup method when no keys are found."""
    mock_redis = MagicMock()
    
    class EmptyAsyncIterMock:
        def __aiter__(self) -> "EmptyAsyncIterMock":
            return self
            
        async def __anext__(self) -> str:
            raise StopAsyncIteration
    
    mock_redis.scan_iter = lambda pattern: EmptyAsyncIterMock()
    mock_redis.delete = AsyncMock()
    
    token_storage = RedisTokenStorage(mock_redis)
    
    await token_storage.cleanup()
    
    mock_redis.delete.assert_not_called()

@pytest.mark.asyncio
async def test_redis_token_storage_cleanup_error() -> None:
    """Test error handling in RedisTokenStorage.cleanup method."""
    mock_redis = MagicMock()
    
    def raise_error(pattern: str) -> None:
        raise ResponseError("Redis command error")
    
    mock_redis.scan_iter = raise_error
    
    token_storage = RedisTokenStorage(mock_redis)
    
    with pytest.raises(TokenStorageError) as exc_info:
        await token_storage.cleanup()
    
    assert "Failed to cleanup tokens" in str(exc_info.value)
    assert "Redis command error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_key_method() -> None:
    """Test the _get_key method of RedisTokenStorage."""
    mock_redis = MagicMock()
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_token"
    settings = get_settings()
    
    key = token_storage._get_key(token)
    
    expected_key = f"{settings.redis_prefix}{token}"
    assert key == expected_key 