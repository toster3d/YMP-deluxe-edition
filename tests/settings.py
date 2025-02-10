from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

from resources.pydantic_schemas import RegisterSchema

TEST_DIR = Path(__file__).parent
DB_FILE = TEST_DIR / "test.db"

class TestSettings(BaseSettings):
    # SQLite settings
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_FILE}"
    ASYNC_DATABASE_URI: str = DATABASE_URL
    
    # Redis settings dla blacklisty JWT
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 1
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    JWT_BLACKLIST_PREFIX: str = "blacklist:"
    JWT_EXPIRATION: int = 3600
    
    # JWT Settings
    JWT_SECRET_KEY: str = "test_key"
    
    TEST_USER: RegisterSchema = RegisterSchema(
        email="test@example.com",
        username="testuser",
        password="Test123!",
        confirmation="Test123!"
    )
    
    # Debug Settings
    DEBUG: bool = True
    
    model_config = {
        "env_file": ".env.test",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
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

test_settings = TestSettings() 