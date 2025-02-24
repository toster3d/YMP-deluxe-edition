from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

TEST_DIR = Path(__file__).parent

class TestSettings(BaseSettings):
    """Test settings configuration."""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    ASYNC_DATABASE_URI: str = DATABASE_URL
    SQLITE_PRAGMA: str = "PRAGMA foreign_keys=ON"  # Enforce foreign key support
    
    # Dodajemy nowe ustawienia dla testów
    TEST_DB_ECHO: bool = False  # Wyłączamy echo dla testów
    TEST_DB_POOL_SIZE: int = 5
    TEST_DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 1
    REDIS_PREFIX: str = "token_blacklist:"
    REDIS_BLACKLIST_VALUE: str = "blacklisted"
    
    # JWT
    JWT_SECRET_KEY: str = "test_secret_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES: int = 30
    
    # Test user
    TEST_USER_EMAIL: str = "test@example.com"
    TEST_USER_PASSWORD: str = "Test123!"
    TEST_USER_NAME: str = "TestUser"
    
    # Debug
    DEBUG: bool = True

    # Python path
    PYTHONPATH: str = "."

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        
@lru_cache
def get_test_settings() -> TestSettings:
    """Get test settings."""
    return TestSettings()
