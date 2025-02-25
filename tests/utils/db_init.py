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
        
        # Wyczyść bazę przed testami
        await redis.flushdb()
        
        # Dodaj testowe dane
        await redis.setex("test_init_key", 3600, "test_init_value")
        await redis.setex("jwt_blacklist:test", 3600, "blacklisted")
        
        # Wyświetl instrukcje na początku testów
        logger.info("\n=== Redis CLI Testing Instructions ===")
        logger.info("1. Connect to Redis CLI:")
        logger.info("   docker exec -it your_project_test-redis redis-cli")
        logger.info("\n2. Try these commands:")
        logger.info("   KEYS *")
        logger.info("   GET test_init_key")
        logger.info("   TTL test_init_key")
        logger.info("   GET jwt_blacklist:test")
        logger.info("   TTL jwt_blacklist:test")
        logger.info("===================================\n")
        
        await redis.close()
        return True
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")
        return False

async def init_test_databases() -> bool:
    """Initialize all test databases."""
    return await init_test_redis() 

