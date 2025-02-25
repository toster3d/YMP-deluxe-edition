# from datetime import timedelta

# import pytest

# from jwt_utils import create_access_token
# from token_blacklist import add_to_blacklist, is_token_blacklisted
# from token_storage import RedisTokenStorage


# @pytest.mark.asyncio
# async def test_blacklist_token(mock_redis: Redis) -> None: #type: ignore    
#     # Arrange
#     token_storage = RedisTokenStorage(mock_redis)
#     user_id: int = 1
#     username: str = "testuser"
#     token: str = create_access_token(user_id, username)
    
#     # Act
#     await add_to_blacklist(token, timedelta(minutes=30), token_storage)
#     is_blacklisted = await is_token_blacklisted(token, token_storage)
    
#     # Assert
#     assert is_blacklisted is True 