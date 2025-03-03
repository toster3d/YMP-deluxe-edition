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
async def test_logout_success(async_client: AsyncClient, auth_token: str) -> None:
    """Test successful logout."""  
    # Arrange
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Act
    logging.info(f"Sending logout request with token: {auth_token[:10]}...")
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK, f"Unexpected status code: {response.status_code}, response: {response.text}"
    assert response.json() == {"message": "Logout successful!"}


@pytest.mark.asyncio
async def test_logout_without_token(async_client: AsyncClient) -> None:
    """Test logout attempt without an authorization token."""
    # Act
    response = await async_client.post("/auth/logout")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_with_invalid_token(async_client: AsyncClient) -> None:
    """Test logout attempt with an invalid token."""
    # Arrange
    headers = {"Authorization": "Bearer invalid_token"}
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_logout_with_expired_token(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test logout attempt with an expired token."""
    # Arrange
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
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_logout_token_without_jti(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test logout attempt with a token without a JTI identifier."""
    # Arrange
    import inspect
    from datetime import datetime, timedelta, timezone

    import jwt

    from src.config import get_settings
    from src.jwt_utils import create_access_token
    
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
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    assert "detail" in response.json()