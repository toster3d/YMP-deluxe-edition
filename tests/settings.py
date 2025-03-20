from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

TEST_DIR = Path(__file__).parent
    
class TestSettings(BaseSettings):
    """Test settings configuration."""
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    ASYNC_DATABASE_URI: str = DATABASE_URL
    SQLITE_PRAGMA: str = "PRAGMA foreign_keys=ON"

    REDIS_HOST: str = "test-redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PREFIX: str = "token_blacklist:"
    REDIS_BLACKLIST_VALUE: str = "blacklisted"
    
    JWT_SECRET_KEY: str = "test_secret_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES: int = 30
    
    TEST_USER_EMAIL: str = "test@example.com"
    TEST_USER_PASSWORD: str = "Test123!"
    TEST_USER_NAME: str = "TestUser"
    
    DEBUG: bool = True

    PYTHONPATH: str = "."

    model_config = {
        "env_file": ".env.test",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        
@lru_cache
def get_test_settings() -> TestSettings:
    """Get test settings."""
    return TestSettings() 