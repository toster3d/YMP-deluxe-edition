import logging
from abc import ABC, abstractmethod
from datetime import timedelta

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class TokenStorageError(Exception):
    """Base exception for token storage errors."""
    pass

class TokenStorage(ABC):
    @abstractmethod
    async def store(self, token_id: str, expires_delta: timedelta) -> None:
        """Store token in blacklist."""
        pass

    @abstractmethod
    async def exists(self, token_id: str) -> bool:
        """Check if token exists in blacklist."""
        pass

class RedisTokenStorage(TokenStorage):
    def __init__(self, redis_client: Redis[str]) -> None:
        self.redis = redis_client
        self.prefix = settings.redis_prefix

    async def store(self, token_id: str, expires_delta: timedelta) -> None:
        """
        Store token in blacklist.
        
        Args:
            token_id: Token identifier (jti)
            expires_delta: Token expiration time
            
        Raises:
            TokenStorageError: If token cannot be stored
        """
        try:
            await self.redis.setex(
                f'{self.prefix}{token_id}', 
                int(expires_delta.total_seconds()), 
                'true'
            )
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error while storing token: {e}")
            raise TokenStorageError(f"Failed to store token: {str(e)}")

    async def exists(self, token_id: str) -> bool:
        """
        Check if token exists in blacklist.
        
        Args:
            token_id: Token identifier (jti)
            
        Returns:
            bool: True if token is blacklisted
            
        Raises:
            TokenStorageError: If token cannot be checked
        """
        try:
            result = await self.redis.exists(f'{self.prefix}{token_id}')
            return bool(result)
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error while checking token: {e}")
            raise TokenStorageError(f"Failed to check token: {str(e)}")

    async def cleanup(self) -> None:
        """Remove expired tokens from blacklist."""
        try:
            await self.redis.delete(
                *[key async for key in self.redis.scan_iter(f"{self.prefix}*")]
            )
        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.error(f"Redis error during cleanup: {e}")
            raise TokenStorageError(f"Failed to cleanup tokens: {str(e)}")

