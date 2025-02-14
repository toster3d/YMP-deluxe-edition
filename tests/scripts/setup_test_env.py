import asyncio
import logging
import subprocess
from pathlib import Path
from typing import NoReturn

from redis.asyncio import Redis
from settings import get_test_settings
from utils.db_init import init_test_databases

logger = logging.getLogger(__name__)

async def wait_for_redis(max_retries: int = 5, retry_delay: int = 1) -> bool:
    """Wait for Redis to be ready."""
    for attempt in range(max_retries):
        try:
            redis = Redis(
                host=get_test_settings().REDIS_HOST,
                port=get_test_settings().REDIS_PORT,
                db=get_test_settings().REDIS_DB,
                decode_responses=True
            )
            await redis.ping()
            await redis.close()
            return True
        except Exception as e:
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(retry_delay)
    return False

async def setup_test_environment() -> bool:
    """Initialize test environment with Docker containers."""
    docker_compose_path = Path(__file__).parents[2] / "docker-compose.test.yml"
    
    try:
        subprocess.run(
            ["docker-compose", "-f", str(docker_compose_path), "up", "-d"],
            check=True,
            capture_output=True
        )
        
        logger.info("Waiting for services to be ready...")
        redis_ready = await wait_for_redis()
        
        if not redis_ready:
            logger.error("Redis failed to start")
            return False
            
        if not await init_test_databases():
            logger.error("Database initialization failed")
            return False
            
        logger.info("Test environment ready")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker command failed: {e.stderr.decode()}")
        return False
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

async def teardown_test_environment() -> None:
    """Clean up test environment."""
    docker_compose_path = Path(__file__).parents[2] / "docker-compose.test.yml"
    try:
        subprocess.run(
            ["docker-compose", "-f", str(docker_compose_path), "down"],
            check=True,
            capture_output=True
        )
        logger.info("Test environment cleaned up")
    except subprocess.CalledProcessError as e:
        logger.error(f"Cleanup failed: {e.stderr.decode()}")

def main() -> NoReturn:
    """Main entry point for test environment setup."""
    logging.basicConfig(level=logging.INFO)
    
    async def run() -> None:
        if await setup_test_environment():
            logger.info("Setup completed successfully")
        else:
            logger.error("Setup failed")
            await teardown_test_environment()
            raise SystemExit(1)
    
    asyncio.run(run())
    raise SystemExit(0)

if __name__ == "__main__":
    main() 