from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

TEST_DIR = Path(__file__).parent
    
class AppTestSettings(BaseSettings):
    """Test settings configuration."""
    
    ASYNC_DATABASE_URI: str = ""
    
    TEST_USER_EMAIL: EmailStr = "test@example.com"
    TEST_USER_PASSWORD: str = "Test123!"
    TEST_USER_NAME: str = "TestUser"

    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8"
    )
        
@lru_cache
def get_test_settings() -> AppTestSettings:
    """Get test settings."""
    return AppTestSettings() 