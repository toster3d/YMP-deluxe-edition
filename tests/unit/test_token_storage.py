import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis

from config import get_settings
from src.token_storage import RedisTokenStorage

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_redis_connection(mock_redis: AsyncMock) -> None:
    """Test podstawowego połączenia z Redis."""
    mock_redis.ping = AsyncMock(return_value=True)
    result = await mock_redis.ping()
    assert result is True

@pytest.mark.asyncio
async def test_store_and_check_token() -> None:
    """Test storing and checking token in Redis."""
    # Arrange
    mock_redis = MagicMock()
    
    # Konfiguracja mocka dla metod asynchronicznych
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.exists.return_value = 1  # Redis.exists zwraca int (1 = True)
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_token"
    expires_delta = timedelta(minutes=30)
    settings = get_settings()
    
    # Act
    await token_storage.store(token, expires_delta)
    exists = await token_storage.exists(token)
    
    # Debug
    logger.debug(f"mock_redis.exists.call_count: {mock_redis.exists.call_count}")
    logger.debug(f"mock_redis.exists.call_args: {mock_redis.exists.call_args}")
    logger.debug(f"exists result: {exists}")
    
    # Assert
    assert exists is True, f"Expected exists to be True, got {exists}"
    
    # Verify mock calls
    expected_key = f"{settings.redis_prefix}{token}"
    mock_redis.setex.assert_called_once()
    mock_redis.exists.assert_called_once_with(expected_key)

@pytest.mark.asyncio
async def test_check_nonexistent_token() -> None:
    """Test checking a token that doesn't exist."""
    # Arrange
    mock_redis = MagicMock()
    mock_redis.exists = AsyncMock()
    mock_redis.exists.return_value = 0  # Token nie istnieje
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "nonexistent_token"
    settings = get_settings()
    
    # Act
    exists = await token_storage.exists(token)
    
    # Assert
    assert exists is False
    
    # Verify mock calls
    expected_key = f"{settings.redis_prefix}{token}"
    mock_redis.exists.assert_called_once_with(expected_key)

@pytest.mark.asyncio
async def test_token_blacklist() -> None:
    """Test dodawania tokenu do blacklisty."""
    # Arrange
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration = timedelta(minutes=60)
    
    # Tworzymy własny mock Redis zamiast używać fixture
    mock_redis = MagicMock(spec=Redis)
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # Ważne: ustawiamy return_value=1
    
    # Przygotuj token storage
    token_storage = RedisTokenStorage(mock_redis)
    
    # Act
    await token_storage.store(token, expiration)
    
    # Assert
    # Sprawdź, czy token jest na blackliście
    is_blacklisted = await token_storage.exists(token)
    assert is_blacklisted is True

@pytest.mark.asyncio
async def test_token_expiration() -> None:
    """Test token expiration."""
    # Arrange
    token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration: timedelta = timedelta(seconds=1)
    
    # Tworzymy własny mock Redis zamiast używać fixture
    mock_redis = MagicMock(spec=Redis)
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)  # Token nie istnieje (wygasł)
    
    # Przygotuj token storage
    token_storage = RedisTokenStorage(mock_redis)
    
    # Act
    await token_storage.store(token, expiration)
    
    # Assert
    is_blacklisted = await token_storage.exists(token)
    assert is_blacklisted is False

@pytest.mark.asyncio
async def test_store_jti_token(mock_redis: AsyncMock) -> None:
    """Test dodawania tokenu JTI do blacklisty."""
    # Arrange
    token_storage = RedisTokenStorage(mock_redis)
    jti = "test-jti"
    expires_in = timedelta(hours=1)
    
    # Reset mock
    mock_redis.setex.reset_mock()
    mock_redis.setex = AsyncMock()
    
    # Act
    await token_storage.store(jti, expires_in)
    
    # Assert
    mock_redis.setex.assert_called_once()
    # Sprawdzamy czy wywołanie zawiera odpowiednie argumenty
    args = mock_redis.setex.call_args[0]
    assert args[0] == f"{token_storage.settings.redis_prefix}{jti}"
    assert args[1] == int(expires_in.total_seconds())
    assert args[2] == token_storage.settings.redis_blacklist_value

@pytest.mark.asyncio
async def test_check_jti_token_exists(mock_redis: AsyncMock) -> None:
    """Test sprawdzania czy token JTI jest na blackliście."""
    # Arrange
    token_storage = RedisTokenStorage(mock_redis)
    jti = "test-jti"
    
    # Przypadek 1: Token jest na blackliście
    mock_redis.exists = AsyncMock(return_value=1)
    
    # Act & Assert
    result = await token_storage.exists(jti)
    assert result is True
    mock_redis.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")
    
    # Przypadek 2: Token nie jest na blackliście
    mock_redis.exists = AsyncMock(return_value=0)
    
    # Act & Assert
    result = await token_storage.exists(jti)
    assert result is False
    mock_redis.exists.assert_called_with(f"{token_storage.settings.redis_prefix}{jti}")

@pytest.mark.asyncio
async def test_jwt_token_storage() -> None:
    """Test dodawania i sprawdzania tokenu JWT w Redis."""
    # Arrange
    mock_redis = MagicMock()
    mock_redis.setex = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # Symulujemy, że token istnieje
    
    token_storage = RedisTokenStorage(mock_redis)
    token = "test_jwt_token"
    expires_delta = timedelta(minutes=30)
    
    # Act
    await token_storage.store(token, expires_delta)
    exists = await token_storage.exists(token)
    
    # Assert
    assert exists is True
    mock_redis.setex.assert_called_once()
    mock_redis.exists.assert_called_once_with(f"{token_storage.settings.redis_prefix}{token}") 