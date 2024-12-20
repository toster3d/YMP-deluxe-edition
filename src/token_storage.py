import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import AsyncIterator

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TokenStorageError(Exception):
    """Base exception for token storage errors."""
    pass


class TokenStorage(ABC):
    """Abstract base class for token storage."""
    
    @abstractmethod
    async def store(self, token: str, expires_delta: timedelta) -> None:
        """Store token with expiration time."""
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, token: str) -> bool:
        """Check if token exists in storage."""
        raise NotImplementedError()


class RedisTokenStorage(TokenStorage):
    """Redis implementation of token storage."""
    
    def __init__(self, redis_client: Redis) -> None:  # type: ignore[type-arg]
        """Initialize Redis token storage."""
        self.redis = redis_client  # type: ignore
        self.prefix = settings.redis_prefix

    async def store(self, token: str, expires_delta: timedelta) -> None:
        """Store token in Redis with expiration time."""
        try:
            await self.redis.setex( # type: ignore
                f'{self.prefix}{token}', 
                int(expires_delta.total_seconds()), 
                'blacklisted'
            )
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error while storing token: {e}")
            raise TokenStorageError(f"Failed to store token: {str(e)}")

    async def exists(self, token: str) -> bool:
        """Check if token exists in Redis."""
        try:
            result = await self.redis.exists(f'{self.prefix}{token}') # type: ignore
            return bool(result)
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error while checking token: {e}")
            raise TokenStorageError(f"Failed to check token: {str(e)}")

    async def cleanup(self) -> None:
        """Remove expired tokens from blacklist."""
        try:
            async_iter: AsyncIterator[str] = self.redis.scan_iter(f"{self.prefix}*") # type: ignore
            keys: list[str] = [key async for key in async_iter]
            if keys:
                await self.redis.delete(*keys) # type: ignore
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error during cleanup: {e}")
            raise TokenStorageError(f"Failed to cleanup tokens: {str(e)}")

