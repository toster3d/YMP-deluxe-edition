import os
from datetime import timedelta
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettingsValidation:
    def test_settings_defaults(self) -> None:
        with patch.dict(os.environ, {
            "DEBUG": "false",
            "ASYNC_DATABASE_URI": "postgresql+asyncpg://postgres:postgres@localhost:5432/recipes",
        }, clear=False):
            settings = get_settings()
            assert settings.debug is False
            assert settings.host == "0.0.0.0"
            assert settings.port == 5000
            assert settings.cors_origins == ["*"]
            assert settings.redis_host == "redis"
            assert settings.jwt_algorithm == "HS256"
            assert settings.jwt_access_token_expires == timedelta(minutes=30)
            assert settings.allowed_hosts == ["localhost", "127.0.0.1"]
            assert settings.redis_pool_size == 10

    def test_settings_from_env(self) -> None:
        with patch.dict(os.environ, {
            "DEBUG": "true", 
            "HOST": "127.0.0.1",
            "PORT": "8080",
            "ALLOWED_HOSTS": '["example.com", "test.com"]',
            "REDIS_POOL_SIZE": "20"
        }, clear=False):
            settings = get_settings()
            assert settings.debug is True
            assert settings.host == "127.0.0.1"
            assert settings.port == 8080
            assert settings.allowed_hosts == ["example.com", "test.com"]
            assert settings.redis_pool_size == 20

    @pytest.mark.parametrize("test_value,expected_minutes", [
        ("5", 5),
        ("60", 60),
        ("720", 720),
        ("1440", 1440)
    ])
    def test_jwt_expiration_valid_values(self, test_value: str, expected_minutes: int) -> None:
        with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": test_value}, clear=False):
            settings = get_settings()
            assert settings.jwt_access_token_expires == timedelta(minutes=expected_minutes)

    @pytest.mark.parametrize("test_value,error_message", [
        ("0", "JWT expiration must be at least 1 minute"),
        ("1500", "JWT expiration must not exceed 24 hours"),
        ("not_a_number", "Invalid JWT expiration format"),
        ("0.5", "Invalid JWT expiration format")
    ])
    def test_jwt_expiration_invalid_values(self, test_value: str, error_message: str) -> None:
        with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": test_value}, clear=False):
            with pytest.raises(ValidationError) as excinfo:
                get_settings()
            assert error_message in str(excinfo.value)

    @pytest.mark.parametrize("test_value", [
        "HS256", "HS384", "HS512", "RS256", "RS384", "RS512"
    ])
    def test_jwt_algorithm_valid_values(self, test_value: str) -> None:
        with patch.dict(os.environ, {"JWT_ALGORITHM": test_value}, clear=False):
            settings = get_settings()
            assert settings.jwt_algorithm == test_value

    def test_jwt_algorithm_invalid_value(self) -> None:
        with patch.dict(os.environ, {"JWT_ALGORITHM": "INVALID_ALG"}, clear=False):
            with pytest.raises(ValidationError):
                get_settings()

    @pytest.mark.parametrize("test_value,expected", [
        ("0", 0),
        ("15", 15),
        ("16", 16)
    ])
    def test_redis_db_valid_values(self, test_value: str, expected: int) -> None:
        with patch.dict(os.environ, {"REDIS_DB": test_value}, clear=False):
            settings = get_settings()
            assert settings.redis_db == expected

    def test_redis_db_invalid_value(self) -> None:
        with patch.dict(os.environ, {"REDIS_DB": "-1"}, clear=False):
            with pytest.raises(ValidationError):
                get_settings()

    @pytest.mark.parametrize("test_value,expected", [
        ('["http://localhost:3000", "https://example.com"]', 
         ["http://localhost:3000", "https://example.com"]),
        ('["*"]', ["*"]),
        ('[]', [])
    ])
    def test_cors_origins_valid_values(self, test_value: str, expected: list[str]) -> None:
        with patch.dict(os.environ, {"CORS_ORIGINS": test_value}, clear=False):
            settings = get_settings()
            assert settings.cors_origins == expected

    @pytest.mark.parametrize("test_value,expected", [
        ("10", 10),
        ("20", 20),
        ("100", 100)
    ])
    def test_positive_integers_valid_values(self, test_value: str, expected: int) -> None:
        with patch.dict(os.environ, {
            "REDIS_PORT": test_value,
            "PORT": test_value,
            "DB_POOL_SIZE": test_value,
            "DB_MAX_OVERFLOW": test_value,
            "REDIS_POOL_SIZE": test_value
        }, clear=False):
            settings = get_settings()
            assert settings.redis_port == expected
            assert settings.port == expected
            assert settings.pool_size == expected
            assert settings.max_overflow == expected
            assert settings.redis_pool_size == expected

    @pytest.mark.parametrize("test_value", [
        "0", "-1", "-10", "not_a_number"
    ])
    def test_positive_integers_invalid_values(self, test_value: str) -> None:
        with patch.dict(os.environ, {
            "REDIS_PORT": test_value,
            "PORT": test_value,
            "DB_POOL_SIZE": test_value,
            "DB_MAX_OVERFLOW": test_value,
            "REDIS_POOL_SIZE": test_value
        }, clear=False):
            with pytest.raises(ValidationError):
                get_settings()

    def test_secretstr_fields(self) -> None:
        test_secrets = {
            "SECRET_KEY": "test-secret-key",
            "JWT_SECRET_KEY": "test-jwt-secret"
        }
        
        with patch.dict(os.environ, test_secrets, clear=False):
            settings = get_settings()
            assert "test-secret-key" not in str(settings.secret_key)
            assert "test-jwt-secret" not in str(settings.jwt_secret_key)
            assert settings.secret_key.get_secret_value() == "test-secret-key"
            assert settings.jwt_secret_key.get_secret_value() == "test-jwt-secret"

    def test_get_settings_singleton(self) -> None:
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is not settings2
        assert isinstance(settings1, Settings)
        assert isinstance(settings2, Settings)

    def test_env_variables_override_defaults(self) -> None:
        test_env = {
            "REDIS_HOST": "custom-redis",
            "REDIS_PORT": "7000",
            "REDIS_DB": "5",
            "REDIS_PREFIX": "custom-prefix:",
            "JWT_ALGORITHM": "RS256",
            "ASYNC_DATABASE_URI": "postgresql+asyncpg://user:pass@host:5433/testdb",
            "ALLOWED_HOSTS": '["custom-host.com"]',
            "REDIS_POOL_SIZE": "50"
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            settings = get_settings()
            assert settings.redis_host == "custom-redis"
            assert settings.redis_port == 7000
            assert settings.redis_db == 5
            assert settings.redis_prefix == "custom-prefix:"
            assert settings.jwt_algorithm == "RS256"
            assert settings.async_database_uri == "postgresql+asyncpg://user:pass@host:5433/testdb"
            assert settings.allowed_hosts == ["custom-host.com"]
            assert settings.redis_pool_size == 50
