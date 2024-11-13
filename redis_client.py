from typing import Optional
from datetime import timedelta
import redis
from flask import current_app
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

class RedisClient:
    _instance: Optional['RedisClient'] = None

    @classmethod
    def new(cls) -> 'RedisClient':
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialized = False
        return cls._instance

    def init(self) -> None:
        if not getattr(self, 'initialized', False):
            self.redis: redis.Redis = redis.Redis(
                host=current_app.config['REDIS_HOST'],
                port=current_app.config['REDIS_PORT'],
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

redis_client: RedisClient = RedisClient()