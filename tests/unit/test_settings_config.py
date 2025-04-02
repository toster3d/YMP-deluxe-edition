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
    env_backup: dict[str, str] = {}
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
    get_test_settings.cache_clear()
    yield
    get_test_settings.cache_clear()


class TestSettingsConfig:
    
    def test_default_values(self, cleanup_env: None) -> None:
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
        os.environ["ASYNC_DATABASE_URI"] = "sqlite+aiosqlite:///test_env.db"
        os.environ["TEST_USER_EMAIL"] = "env_test@example.com"
        os.environ["TEST_USER_NAME"] = "EnvTestUser"
        os.environ["TEST_USER_PASSWORD"] = "NewPassword123!"
        os.environ["DEBUG"] = "False"
        
        settings = AppTestSettings()
        
        assert settings.ASYNC_DATABASE_URI == "sqlite+aiosqlite:///test_env.db"
        assert settings.TEST_USER_EMAIL == "env_test@example.com"
        assert settings.TEST_USER_NAME == "EnvTestUser"
        assert settings.TEST_USER_PASSWORD == "NewPassword123!"
        assert settings.DEBUG is False
    
    def test_env_file_loading(self, cleanup_env: None, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        env_file = tmp_path / ".env.test"
        env_file.write_text(
            "TEST_USER_EMAIL=envfile@example.com\n"
            "TEST_USER_PASSWORD=EnvFile123!\n"
        )
        
        monkeypatch.chdir(tmp_path)
        
        for key in ['TEST_USER_EMAIL', 'TEST_USER_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        settings = AppTestSettings()
        
        assert settings.TEST_USER_EMAIL == "envfile@example.com"
        assert settings.TEST_USER_PASSWORD == "EnvFile123!"
    
    def test_email_validation(self, cleanup_env: None) -> None:
        with pytest.raises(ValidationError) as exc_info:
            AppTestSettings(TEST_USER_EMAIL="invalid-email-address")
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_email_validation_none(self, cleanup_env: None) -> None:
        with pytest.raises(ValidationError) as exc_info:
            AppTestSettings(TEST_USER_EMAIL=None)
        
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_bool_conversion(self, cleanup_env: None) -> None:
        test_cases = [
            ("true", True), 
            ("True", True), 
            ("1", True), 
            ("yes", True),
            ("false", False), 
            ("False", False), 
            ("0", False), 
            ("no", False)
        ]
        
        for str_value, expected_bool in test_cases:
            os.environ["DEBUG"] = str_value
            settings = AppTestSettings()
            assert settings.DEBUG is expected_bool, f"Failed for '{str_value}'"
    
    def test_settings_cache(self, clear_settings_cache: None) -> None:
        settings1 = get_test_settings()
        settings2 = get_test_settings()
        
        assert settings1 is settings2
    
    def test_settings_cache_clear(self, clear_settings_cache: None) -> None:
        settings1 = get_test_settings()
        
        get_test_settings.cache_clear()
        
        settings2 = get_test_settings()
        
        assert settings1 is not settings2
    
    def test_environment_variable_precedence(self, cleanup_env: None, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        env_file = tmp_path / ".env.test"
        env_file.write_text(
            "TEST_USER_EMAIL=envfile@example.com\n"
            "TEST_USER_PASSWORD=EnvFile123!\n"
        )
        
        monkeypatch.chdir(tmp_path)
        
        os.environ["TEST_USER_EMAIL"] = "env_var@example.com"
        
        settings = AppTestSettings()
        
        assert settings.TEST_USER_EMAIL == "env_var@example.com"
        assert settings.TEST_USER_PASSWORD == "EnvFile123!"
    
    def test_invalid_database_uri(self, cleanup_env: None) -> None:
        os.environ["ASYNC_DATABASE_URI"] = "invalid://invalid/invalid"
        
        settings = AppTestSettings()
        assert settings.ASYNC_DATABASE_URI == "invalid://invalid/invalid"

@pytest.mark.usefixtures("cleanup_env", "clear_settings_cache")
def test_settings_defaults_standalone() -> None:
    keys_to_remove = ['ASYNC_DATABASE_URI', 'TEST_USER_EMAIL', 'TEST_USER_NAME', 'TEST_USER_PASSWORD', 'DEBUG']
    backup: dict[str, str] = {}
    
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
        for key, value in backup.items():
            os.environ[key] = value