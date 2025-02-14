from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

TEST_DIR = Path(__file__).parent
DB_FILE = TEST_DIR / "test.db"

class TestSettings(BaseSettings):
    """Test settings configuration."""
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_FILE}"
    ASYNC_DATABASE_URI: str = DATABASE_URL

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

    model_config = {
        "env_file": ".env.test",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "allow"
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        
    async def cleanup(self) -> None:
        """Cleanup after tests"""
        try:
            if DB_FILE.exists():
                DB_FILE.unlink()
        except Exception as e:
            print(f"Error during cleanup of the test database: {e}")

#@lru_cache
def get_test_settings() -> TestSettings:
    """Get test settings."""
    return TestSettings() 