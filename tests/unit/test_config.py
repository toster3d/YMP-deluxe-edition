import os
from datetime import timedelta
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Test if settings load with default values correctly."""
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


def test_settings_from_env() -> None:
    """Test if settings load from environment variables correctly."""
    with patch.dict(os.environ, {
        "DEBUG": "true", 
        "HOST": "127.0.0.1",
        "PORT": "8080"
    }, clear=False):
        settings = get_settings()
        assert settings.debug is True
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080


@pytest.mark.parametrize("test_value", [
    "5",  # 5 minutes
    "60",  # 60 minutes
    "720"  # 12 hours
])
def test_jwt_expiration_valid_values(test_value: str) -> None:
    """Test JWT expiration with valid string values."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": test_value}, clear=False):
        settings = get_settings()
        assert settings.jwt_access_token_expires == timedelta(minutes=int(test_value))


def test_jwt_expiration_too_short() -> None:
    """Test JWT expiration with value that's too short."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": "0"}, clear=False):
        with pytest.raises(ValidationError) as excinfo:
            get_settings()
        assert "JWT expiration must be at least 1 minute" in str(excinfo.value)


def test_jwt_expiration_too_long() -> None:
    """Test JWT expiration with value that's too long."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": "1500"}, clear=False):  # 25 hours
        with pytest.raises(ValidationError) as excinfo:
            get_settings()
        assert "JWT expiration must not exceed 24 hours" in str(excinfo.value)


def test_jwt_expiration_string_valid() -> None:
    """Test JWT expiration with valid string value."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": "120"}, clear=False):
        settings = get_settings()
        assert settings.jwt_access_token_expires == timedelta(minutes=120)


def test_jwt_expiration_string_invalid() -> None:
    """Test JWT expiration with invalid string value."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": "not_a_number"}, clear=False):
        with pytest.raises(ValidationError) as excinfo:
            get_settings()
        assert "Invalid JWT expiration format" in str(excinfo.value)


def test_jwt_expiration_invalid_format_decimal() -> None:
    """Test JWT expiration with invalid decimal format."""
    with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRES": "0.5"}, clear=False):
        with pytest.raises(ValidationError) as excinfo:
            get_settings()
        assert "Invalid JWT expiration format" in str(excinfo.value)
        assert "invalid literal for int()" in str(excinfo.value)


def test_redis_prefix_pattern() -> None:
    """Test validation of Redis prefix pattern."""
    with patch.dict(os.environ, {"REDIS_PREFIX": "valid_prefix:"}, clear=False):
        settings = get_settings()
        assert settings.redis_prefix == "valid_prefix:"
    
    with patch.dict(os.environ, {"REDIS_PREFIX": "invalid_prefix"}, clear=False):
        with pytest.raises(ValidationError):
            get_settings()


def test_jwt_algorithm_validation() -> None:
    """Test validation of JWT algorithm pattern."""
    valid_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
    
    for algorithm in valid_algorithms:
        with patch.dict(os.environ, {"JWT_ALGORITHM": algorithm}, clear=False):
            settings = get_settings()
            assert settings.jwt_algorithm == algorithm
    
    with patch.dict(os.environ, {"JWT_ALGORITHM": "INVALID_ALG"}, clear=False):
        with pytest.raises(ValidationError):
            get_settings()


def test_secretstr_fields() -> None:
    """Test that SecretStr fields are properly handled."""
    with patch.dict(os.environ, {
        "SECRET_KEY": "test-secret-key",
        "JWT_SECRET_KEY": "test-jwt-secret"
    }, clear=False):
        settings = get_settings()
        
        assert "test-secret-key" not in str(settings.secret_key)
        assert "test-jwt-secret" not in str(settings.jwt_secret_key)
        
        assert settings.secret_key.get_secret_value() == "test-secret-key"
        assert settings.jwt_secret_key.get_secret_value() == "test-jwt-secret"


def test_positive_integers() -> None:
    """Test validation of PositiveInt fields."""
    with patch.dict(os.environ, {
        "REDIS_PORT": "8000",
        "PORT": "8080",
        "DB_POOL_SIZE": "10",
        "DB_MAX_OVERFLOW": "20"
    }, clear=False):
        settings = get_settings()
        assert settings.redis_port == 8000
        assert settings.port == 8080
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
    
    with patch.dict(os.environ, {"REDIS_PORT": "0"}, clear=False):
        with pytest.raises(ValidationError):
            get_settings()
    
    with patch.dict(os.environ, {"PORT": "-1"}, clear=False):
        with pytest.raises(ValidationError):
            get_settings()


def test_redis_db_validation() -> None:
    """Test validation of Redis DB number."""
    with patch.dict(os.environ, {"REDIS_DB": "0"}, clear=False):
        settings = get_settings()
        assert settings.redis_db == 0
    
    with patch.dict(os.environ, {"REDIS_DB": "15"}, clear=False):
        settings = get_settings()
        assert settings.redis_db == 15
    
    with patch.dict(os.environ, {"REDIS_DB": "-1"}, clear=False):
        with pytest.raises(ValidationError):
            get_settings()


def test_cors_origins_parsing() -> None:
    """Test parsing of CORS origins from environment variable."""
    test_origins = ["http://localhost:3000", "https://example.com"]
    
    with patch.dict(os.environ, {"CORS_ORIGINS": '["http://localhost:3000", "https://example.com"]'}, clear=False):
        settings = get_settings()
        assert settings.cors_origins == test_origins


def test_get_settings_function() -> None:
    """Test that get_settings function returns Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert get_settings() is not get_settings()


def test_env_variables_override_defaults() -> None:
    """Test that environment variables override default values."""
    with patch.dict(os.environ, {
        "REDIS_HOST": "custom-redis",
        "REDIS_PORT": "7000",
        "REDIS_DB": "5",
        "REDIS_PREFIX": "custom-prefix:",
        "JWT_ALGORITHM": "RS256",
        "ASYNC_DATABASE_URI": "postgresql+asyncpg://user:pass@host:5433/testdb"
    }, clear=False):
        settings = get_settings()
        assert settings.redis_host == "custom-redis"
        assert settings.redis_port == 7000
        assert settings.redis_db == 5
        assert settings.redis_prefix == "custom-prefix:"
        assert settings.jwt_algorithm == "RS256"
        assert settings.async_database_uri == "postgresql+asyncpg://user:pass@host:5433/testdb"
