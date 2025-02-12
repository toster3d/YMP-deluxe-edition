import logging

from redis.asyncio import Redis
from settings import get_test_settings

logger = logging.getLogger(__name__)
settings = get_test_settings()

async def init_test_redis() -> bool:
    """Initialize test Redis instance."""
    try:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        await redis.ping()
        await redis.flushdb()  # Clear test database
        await redis.close()
        return True
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")
        return False

async def init_test_databases() -> bool:
    """Initialize all test databases."""
    return await init_test_redis() 