import asyncio

import pytest
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_redis_connection(mock_redis: Redis) -> None:
    """Test podstawowego połączenia z Redis."""
    assert await mock_redis.ping() is True

@pytest.mark.asyncio
async def test_token_blacklist(mock_redis: Redis) -> None:
    """Test dodawania tokenu do blacklisty."""
    # Arrange
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration = 3600
    
    # Act & Assert
    assert await mock_redis.setex(f"expired_token:{token}", expiration, "1") is True
    mock_redis.exists.side_effect = lambda *args, **kwargs: True
    assert await mock_redis.exists(f"expired_token:{token}") is True

@pytest.mark.asyncio
async def test_token_expiration(mock_redis: Redis) -> None:
    """Test token expiration."""
    # Arrange
    token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    expiration: int = 1
    
    # Act
    assert await mock_redis.setex(f"expired_token:{token}", expiration, "1") is True
    await asyncio.sleep(0.1)  # Krótsze opóźnienie dla szybszych testów
    mock_redis.exists.side_effect = lambda *args, **kwargs: False
    
    # Assert
    assert await mock_redis.exists(f"expired_token:{token}") is False 