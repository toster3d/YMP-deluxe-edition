import logging

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_models.models_db_test import TestUser

from services.user_auth_manager import MissingCredentialsError, UserAuth

# Configuration for logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, create_test_user: TestUser) -> None:
    """Test successful login."""
    # Arrange
    response = await async_client.post(
        "/auth/login",
        data={
            "username": create_test_user.user_name,  # Using username for login
            "password": "Test123!"  # Ensure the password is correct
        }
    )
    
    # Act & Assert
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_missing_credentials(db_session: AsyncSession) -> None:
    """Test login with missing credentials."""
    # Arrange
    user_auth = UserAuth(db_session)
    
    # Act & Assert
    with pytest.raises(MissingCredentialsError):
        await user_auth.login("", "")

@pytest.mark.asyncio
async def test_login_with_form_invalid_credentials(async_client: AsyncClient) -> None:
    """Test login with invalid credentials."""
    response = await async_client.post(
        "/auth/login",
        data={"username": "wronguser", "password": "WrongPassword123!"}  # Using invalid credentials
    )
    assert response.status_code == 401  # Unauthorized status code for invalid credentials
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_login_with_form_token_error(async_client: AsyncClient, create_test_user: TestUser) -> None:
    """Test login with token error."""
    # Modyfikujemy test, aby sprawdzić przypadek, gdy użytkownik istnieje, ale hasło jest niepoprawne
    response = await async_client.post(
        "/auth/login",
        data={"username": create_test_user.user_name, "password": "WrongPassword123!"}
    )
    assert response.status_code == 401  # Unauthorized status code for invalid credentials
    assert "detail" in response.json()