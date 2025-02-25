# import pytest
# from fastapi import HTTPException
# from redis.asyncio import Redis

# from src.dependencies import get_redis


# @pytest.mark.asyncio
# async def test_get_redis_success(mock_redis: Redis) -> None: #type: ignore
#     # Arrange & Act
#     async for redis in get_redis():
#         # Assert
#         assert redis is not None

# @pytest.mark.asyncio
# async def test_get_redis_failure() -> None:
#     # Arrange & Act & Assert
#     with pytest.raises(HTTPException) as exc_info:
#         async for _ in get_redis():
#             pass
#     assert exc_info.value.status_code == 503 