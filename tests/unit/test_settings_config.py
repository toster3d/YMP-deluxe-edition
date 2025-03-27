import importlib
import os
from typing import Any, Generator

import pytest
from pydantic import ValidationError

settings_module = importlib.import_module('tests.settings')
AppTestSettings = settings_module.AppTestSettings
get_test_settings = settings_module.get_test_settings


@pytest.fixture
def cleanup_env() -> Generator[None, None, None]:
    """Stores and restores environment variables after the test."""
    env_backup: dict[str, Any] = {}
    env_keys = [
        'ASYNC_DATABASE_URI',
        'TEST_USER_EMAIL',
        'TEST_USER_NAME',
        'TEST_USER_PASSWORD',
        'DEBUG'
    ]
    
    for key in env_keys:
        if key in os.environ:
            env_backup[key] = os.environ[key]
    
    yield
    
    for key in env_keys:
        if key in env_backup:
            os.environ[key] = env_backup[key]
        elif key in os.environ:
            del os.environ[key]


@pytest.fixture
def clear_settings_cache() -> Generator[None, None, None]:
    """Clears the cache of the get_test_settings() function."""
    get_test_settings.cache_clear()
    yield
    get_test_settings.cache_clear()


class TestSettingsConfig:
    """Tests for the configuration module."""
    
    def test_default_values(self, cleanup_env: None) -> None:
        """Checks if default values are loaded correctly."""
        for key in ['ASYNC_DATABASE_URI', 'TEST_USER_EMAIL', 'TEST_USER_NAME', 'TEST_USER_PASSWORD', 'DEBUG']:
            if key in os.environ:
                del os.environ[key]
        
        settings = AppTestSettings()
        
        assert settings.ASYNC_DATABASE_URI == ""
        assert settings.TEST_USER_EMAIL == "test@example.com"
        assert settings.TEST_USER_PASSWORD == "Test123!"
        assert settings.TEST_USER_NAME == "TestUser"
        assert settings.DEBUG is True
    
    def test_environment_variables(self, cleanup_env: None) -> None:
        """Checks if environment variables are loaded correctly."""
        os.environ["TEST_USER_EMAIL"] = "env_test@example.com"
        os.environ["TEST_USER_NAME"] = "EnvTestUser"
        
        settings = AppTestSettings()
        
        assert settings.TEST_USER_EMAIL == "env_test@example.com"
        assert settings.TEST_USER_NAME == "EnvTestUser"
        
        assert settings.TEST_USER_PASSWORD == "Test123!"
        assert settings.DEBUG is True
    
    def test_email_validation(self, cleanup_env: None) -> None:
        """Checks if email validation works correctly."""
        with pytest.raises(ValidationError) as exc_info:
            AppTestSettings(TEST_USER_EMAIL="invalid-email-address")
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_settings_cache(self, clear_settings_cache: None) -> None:
        """Checks if the get_test_settings() function uses caching."""
        settings1 = get_test_settings()
        settings2 = get_test_settings()
        
        assert settings1 is settings2
    
    def test_settings_cache_clear(self, clear_settings_cache: None) -> None:
        """Checks if clearing the cache works correctly."""
        settings1 = get_test_settings()
        
        get_test_settings.cache_clear()
        
        settings2 = get_test_settings()
        
        assert settings1 is not settings2


@pytest.mark.usefixtures("cleanup_env", "clear_settings_cache")
def test_settings_defaults_standalone() -> None:
    """Checks default settings values without environment variables."""
    keys_to_remove = ['ASYNC_DATABASE_URI', 'TEST_USER_EMAIL', 'TEST_USER_NAME', 'TEST_USER_PASSWORD', 'DEBUG']
    backup = {}
    
    for key in keys_to_remove:
        if key in os.environ:
            backup[key] = os.environ[key]
            del os.environ[key]
    
    try:
        settings = AppTestSettings()
        
        assert settings.ASYNC_DATABASE_URI == ""
        assert settings.TEST_USER_EMAIL == "test@example.com"
        assert settings.TEST_USER_PASSWORD == "Test123!"
        assert settings.TEST_USER_NAME == "TestUser"
        assert settings.DEBUG is True
    finally:
        for key, value in backup.items():  # type: ignore
            os.environ[key] = value