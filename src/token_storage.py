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

    def __init__(self, redis_client: Redis) -> None:  # type: ignore
        """
        Initialize Redis token storage using the provided Redis client.

        :param redis_client: Redis client to interact with the Redis server.
        """
        self.redis = redis_client  # type: ignore
        self.settings = get_settings()

    def _get_key(self, token: str) -> str:
        """Get full Redis key with prefix."""
        return f"{self.settings.redis_prefix}{token}"

    async def store(self, token: str, expires_delta: timedelta) -> None:
        """Store token in Redis with expiration time."""
        try:
            await self.redis.setex(  # type: ignore
                self._get_key(token),
                int(expires_delta.total_seconds()),
                self.settings.redis_blacklist_value
            )
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.exception("Redis error while storing token")
            raise TokenStorageError(f"Failed to store token: {str(e)}")

    async def exists(self, token: str) -> bool:
        """Check if token exists in Redis."""
        try:
            result = await self.redis.exists(self._get_key(token))  # type: ignore
            return bool(result)
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.exception("Redis error while checking token")
            raise TokenStorageError(f"Failed to check token: {str(e)}")

    async def cleanup(self) -> None:
        """Remove expired tokens from blacklist."""
        try:
            pattern = f"{self.settings.redis_prefix}{self.settings.redis_key_pattern}"
            async_iter: AsyncIterator[str] = self.redis.scan_iter(pattern)  # type: ignore
            keys: list[str] = [key async for key in async_iter]
            if keys:
                await self.redis.delete(*keys)  # type: ignore
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.exception("Redis error during cleanup")
            raise TokenStorageError(f"Failed to cleanup tokens: {str(e)}")
