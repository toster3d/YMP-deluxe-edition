import pytest
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_redis_connection(mock_redis: Redis) -> None: #type: ignore
    # Test basic Redis connection
    assert await mock_redis.ping() is True 