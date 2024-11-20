from abc import ABC, abstractmethod
from datetime import timedelta
import redis
from flask import current_app
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

class TokenStorage(ABC):
    @abstractmethod
    def store(self, token_id: str, expires_delta: timedelta) -> None:
        pass

    @abstractmethod
    def exists(self, token_id: str) -> bool:
        pass

class RedisTokenStorage(TokenStorage):
    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client

    def store(self, token_id: str, expires_delta: timedelta) -> None:
        try:
            self.redis.setex(
                f'token_blacklist:{token_id}', 
                int(expires_delta.total_seconds()), 
                'true'
            )
        except (ConnectionError, TimeoutError, ResponseError) as e:
            current_app.logger.error(f"Redis error: {e}")
            raise

    def exists(self, token_id: str) -> bool:
        try:
            return bool(self.redis.exists(f'token_blacklist:{token_id}'))
        except (ConnectionError, TimeoutError, ResponseError) as e:
            current_app.logger.error(f"Redis error: {e}")
            raise
