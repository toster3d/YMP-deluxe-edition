from typing import Optional, cast
from datetime import timedelta
import redis
from flask import current_app
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

class RedisClient:
    _instance: Optional['RedisClient'] = None

    def __new__(cls) -> 'RedisClient':
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, 'initialized', False):
            self.redis: redis.Redis = redis.Redis(
                host=cast(str, current_app.config['REDIS_HOST']),
                port=cast(int, current_app.config['REDIS_PORT']),
                decode_responses=True
            )
            self.initialized = True

    def add_to_blacklist(self, jti: str, expires_delta: timedelta) -> None:
        try:
            self.redis.setex(f'token_blacklist:{jti}', int(expires_delta.total_seconds()), 'true')
        except (ConnectionError, TimeoutError, ResponseError) as e:
            current_app.logger.error(f"Redis error: {e}")
            raise

    def is_blacklisted(self, jti: str) -> bool:
        try:
            return bool(self.redis.exists(f'token_blacklist:{jti}'))
        except (ConnectionError, TimeoutError, ResponseError) as e:
            current_app.logger.error(f"Redis error: {e}")
            raise

#redis_client: RedisClient = RedisClient()