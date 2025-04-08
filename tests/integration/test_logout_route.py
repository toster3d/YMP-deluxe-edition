import inspect
import logging
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import status
from httpx import AsyncClient

from src.config import get_settings
from src.jwt_utils import create_access_token


@pytest.mark.asyncio
class TestLogoutRoute:
    """Tests for /auth/logout route."""

    async def test_logout_success(self, async_client: AsyncClient, auth_token: str) -> None:
        """Test successful logout."""  
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        logging.info(f"Sending logout request with token: {auth_token[:10]}...")
        response = await async_client.post("/auth/logout", headers=headers)
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            assert "Redis connection error" in response.json()["detail"]
        else:
            assert response.json() == {"message": "Logout successful!"}

    async def test_logout_without_token(self, async_client: AsyncClient) -> None:
        """Test logout attempt without an authorization token."""
        response = await async_client.post("/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]

    async def test_logout_with_invalid_token(self, async_client: AsyncClient) -> None:
        """Test logout attempt with an invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await async_client.post("/auth/logout", headers=headers)
        
        assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE]
        assert "detail" in response.json()

    async def test_logout_with_expired_token(self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logout attempt with an expired token."""
        sig = inspect.signature(create_access_token)
        logging.info(f"Signature of create_access_token: {sig}")
        
        settings = get_settings()
        
        expire = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        payload = {
            "sub": "test@example.com",
            "exp": int(expire.timestamp()),
            "iat": int((expire - timedelta(minutes=30)).timestamp()),
            "jti": "test-jti-expired"
        }
        
        expired_token = jwt.encode(
            payload, 
            settings.jwt_secret_key.get_secret_value(), 
            algorithm=settings.jwt_algorithm
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.post("/auth/logout", headers=headers)
        
        assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE]
        assert "detail" in response.json()

    async def test_logout_token_without_jti(self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logout attempt with a token without a JTI identifier."""
        sig = inspect.signature(create_access_token)
        logging.info(f"Signature of create_access_token: {sig}")
        
        settings = get_settings()
        
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        payload = {
            "sub": "test@example.com",
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp())
        }
        
        token_without_jti = jwt.encode(
            payload, 
            settings.jwt_secret_key.get_secret_value(), 
            algorithm=settings.jwt_algorithm
        )
        
        headers = {"Authorization": f"Bearer {token_without_jti}"}
        
        response = await async_client.post("/auth/logout", headers=headers)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST, 
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        assert "detail" in response.json()