from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from fastapi import HTTPException

from src.config import get_settings
from src.jwt_utils import create_access_token, verify_jwt

settings = get_settings()


class TestJWTUtils:
    """Test suite for JWT utilities."""

    @pytest.fixture
    def test_user_data(self) -> dict[str, Any]:
        """Fixture providing test user data."""
        return {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }

    @pytest.fixture
    def valid_token(self, test_user_data: dict[str, Any]) -> str:
        """Fixture providing a valid JWT token."""
        return create_access_token(
            test_user_data["user_id"],
            test_user_data["username"]
        )

    def test_create_and_verify_valid_token(self, test_user_data: dict[str, Any]) -> None:
        """Test creating and verifying a valid token."""
        token = create_access_token(
            test_user_data["user_id"],
            test_user_data["username"]
        )
        payload = verify_jwt(token)

        assert payload["sub"] == str(test_user_data["user_id"])
        assert payload["username"] == test_user_data["username"]
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        assert payload["type"] == "access"

    def test_verify_expired_token(self) -> None:
        """Test verifying an expired token."""
        expired_token = str(jwt.encode(
            {
                "exp": datetime.now(UTC) - timedelta(hours=1),
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "sub": "1",
                "username": "testuser",
                "type": "access",
                "jti": "test-jti"
            },
            settings.jwt_secret_key.get_secret_value(),
            algorithm=settings.jwt_algorithm
        ))

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(expired_token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has expired"

    def test_verify_invalid_token(self) -> None:
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    def test_verify_token_with_wrong_secret(self, valid_token: str) -> None:
        """Test verifying a token with wrong secret key."""
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(valid_token + "tampered")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    def test_token_payload_structure(self, valid_token: str) -> None:
        """Test token payload structure and data types."""
        payload = verify_jwt(valid_token)
        
        assert isinstance(payload["sub"], str)
        assert isinstance(payload["username"], str)
        assert isinstance(payload["exp"], int)
        assert isinstance(payload["iat"], int)
        assert isinstance(payload["jti"], str)
        assert isinstance(payload["type"], str)

    def test_token_expiration_time(self, valid_token: str) -> None:
        """Test token expiration time is set correctly."""
        payload = verify_jwt(valid_token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, UTC)
        
        assert exp_datetime > datetime.now(UTC)
        assert exp_datetime <= datetime.now(UTC) + settings.jwt_access_token_expires

    @pytest.mark.parametrize("user_id,username", [
        (1, "testuser"),
        (999999, "long_username_here"),
        (0, "admin")
    ])
    def test_create_token_with_different_users(
        self, user_id: int, username: str
    ) -> None:
        """Test creating tokens for different users."""
        token = create_access_token(user_id, username)
        payload = verify_jwt(token)
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username

    def test_token_algorithm(self, valid_token: str) -> None:
        """Test token algorithm matches settings."""
        header = jwt.get_unverified_header(valid_token)
        assert header["alg"] == settings.jwt_algorithm

    def test_token_iat_time(self, valid_token: str) -> None:
        """Test token issued at time is recent."""
        payload = verify_jwt(valid_token)
        iat_timestamp = payload["iat"]
        iat_datetime = datetime.fromtimestamp(iat_timestamp, UTC)
        
        assert datetime.now(UTC) - iat_datetime < timedelta(seconds=5) 