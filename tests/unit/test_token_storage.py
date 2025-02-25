import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from config import get_settings
from src.token_storage import RedisTokenStorage

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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