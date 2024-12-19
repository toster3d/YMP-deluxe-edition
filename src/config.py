import os
from datetime import timedelta

from pydantic import Field, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    This class manages all configuration settings for the application,
    including secrets, database connections, and feature flags.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        case_sensitive=False,
        json_schema_extra={
            "example": {
                "secret_key": "your-secret-key",
                "debug": False,
                "jwt_secret_key": "your-jwt-secret",
                "jwt_algorithm": "HS256",
                "redis_host": "localhost",
                "redis_port": 6379
            }
        }
    )
    
    # Basic settings
    secret_key: SecretStr = Field(
        default="change_me_in_production",
        validation_alias="SECRET_KEY",
        description="Secret key for session signing"
    )
    debug: bool = Field(
        default=False,
        validation_alias="DEBUG",
        description="Debug mode flag"
    )

    # JWT Configuration
    jwt_secret_key: SecretStr = Field(
        default="change_me",
        validation_alias="JWT_SECRET_KEY",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
        pattern="^(HS256|HS384|HS512|RS256|RS384|RS512)$",
        description="Algorithm used for JWT signing"
    )
    jwt_access_token_expires: timedelta = Field(
        default=timedelta(minutes=30),
        validation_alias="JWT_ACCESS_TOKEN_EXPIRES",
        description="JWT token expiration time"
    )

    # Database settings
    async_database_uri: str = Field(
        default_factory=lambda: f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'instance', 'recipes.db')}",
        validation_alias="ASYNC_DATABASE_URI",
        description="Async SQLAlchemy database URI"
    )
    sqlalchemy_database_uri: str = Field(
        default_factory=lambda: f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'recipes.db')}",
        validation_alias="DATABASE_URI",
        description="SQLAlchemy database URI"
    )

    # Redis settings
    redis_host: str = Field(
        default="redis",
        validation_alias="REDIS_HOST",
        description="Redis server hostname"
    )
    redis_port: PositiveInt = Field(
        default=6379,
        validation_alias="REDIS_PORT",
        description="Redis server port"
    )
    redis_db: int = Field(
        default=0,
        validation_alias="REDIS_DB",
        ge=0,
        description="Redis database number"
    )
    redis_prefix: str = Field(
        default="token_blacklist:",
        validation_alias="REDIS_PREFIX",
        pattern="^[a-zA-Z0-9_-]+:$",
        description="Prefix for Redis keys"
    )

    # Server settings
    host: str = Field(
        default="0.0.0.0",
        validation_alias="HOST",
        description="Server host"
    )
    port: PositiveInt = Field(
        default=5000,
        validation_alias="PORT",
        description="Server port"
    )
    cors_origins: list[str] = Field(
        default=["*"],
        validation_alias="CORS_ORIGINS",
        description="Allowed CORS origins"
    )

    # Additional database settings
    pool_size: PositiveInt = Field(
        default=5,
        validation_alias="DB_POOL_SIZE",
        description="Database connection pool size"
    )
    max_overflow: PositiveInt = Field(
        default=10,
        validation_alias="DB_MAX_OVERFLOW",
        description="Maximum number of connections that can be created beyond pool_size"
    )

    @field_validator("jwt_access_token_expires", mode="before")
    @classmethod
    def validate_jwt_expires(cls, v: str | timedelta) -> timedelta:
        """Validate that JWT expiration is reasonable."""
        if isinstance(v, str):
            try:
                # Próba konwersji stringa na minuty
                minutes = int(v)
                v = timedelta(minutes=minutes)
            except ValueError as e:
                raise ValueError(f"Invalid JWT expiration format: {e}")
        
        if v.total_seconds() < 60:  # minimum 1 minute
            raise ValueError("JWT expiration must be at least 1 minute")
        if v.total_seconds() > 86400:  # maximum 24 hours
            raise ValueError("JWT expiration must not exceed 24 hours")
        return v


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: Application configuration instance
    """
    return Settings()