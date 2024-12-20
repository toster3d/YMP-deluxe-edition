from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from config import get_settings
from token_storage import RedisTokenStorage

settings = get_settings()

async def get_redis() -> AsyncGenerator[Redis, None]: # type: ignore
    """
    Get Redis client from the pool.
    
    Yields:
        Redis: Redis client instance
        
    Raises:
        HTTPException: If Redis connection fails
    """
    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    try:
        if not await redis_client.ping():
            raise RedisError("Redis ping failed")
        yield redis_client
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection error: {str(e)}"
        )
    finally:
        await redis_client.close()


async def get_token_storage(
    redis: Annotated[Redis, Depends(get_redis)] # type: ignore
) -> RedisTokenStorage:
    """
    Get token storage instance.
    
    Args:
        redis: Redis client instance
        
    Returns:
        RedisTokenStorage: Token storage instance
    """
    return RedisTokenStorage(redis)