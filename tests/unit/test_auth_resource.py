import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from resources.auth_resource import AuthResource
from services.user_auth_manager import (
    InvalidCredentialsError,
    MissingCredentialsError,
    TokenError,
    UserAuth,
)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login_with_form_success() -> None:
    """Test successful login with form data."""
    # Arrange
    mock_user_auth = AsyncMock(spec=UserAuth)
    mock_user_auth.login = AsyncMock(return_value="test_token")
    
    # Create AuthResource with mock UserAuth
    auth_resource = AuthResource(MagicMock())
    auth_resource.user_auth = mock_user_auth
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "password123"
    
    # Act
    result = await auth_resource.login_with_form(form_data)
    
    # Assert
    assert result.access_token == "test_token"
    assert result.token_type == "bearer"
    mock_user_auth.login.assert_called_once_with(username="testuser", password="password123")

@pytest.mark.asyncio
async def test_login_with_form_missing_credentials() -> None:
    """Test login with missing credentials."""
    # Arrange
    mock_user_auth = AsyncMock(spec=UserAuth)
    mock_user_auth.login = AsyncMock(side_effect=MissingCredentialsError())
    
    # Create AuthResource with mock UserAuth
    auth_resource = AuthResource(MagicMock())
    auth_resource.user_auth = mock_user_auth
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = ""
    form_data.password = ""
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Missing credentials" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_with_form_invalid_credentials() -> None:
    """Test login with invalid credentials."""
    # Arrange
    mock_user_auth = AsyncMock(spec=UserAuth)
    mock_user_auth.login = AsyncMock(side_effect=InvalidCredentialsError())
    
    # Create AuthResource with mock UserAuth
    auth_resource = AuthResource(MagicMock())
    auth_resource.user_auth = mock_user_auth
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "wrong_password"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid username or password" in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(username="testuser", password="wrong_password")

@pytest.mark.asyncio
async def test_login_with_form_token_error() -> None:
    """Test login with token generation error."""
    # Arrange
    mock_user_auth = AsyncMock(spec=UserAuth)
    error_message = "Token generation failed"
    mock_user_auth.login = AsyncMock(side_effect=TokenError(error_message))
    
    # Create AuthResource with mock UserAuth
    auth_resource = AuthResource(MagicMock())
    auth_resource.user_auth = mock_user_auth
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "password123"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_message in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(username="testuser", password="password123")

@pytest.mark.asyncio
async def test_login_with_form_unexpected_error() -> None:
    """Test login with unexpected error."""
    # Arrange
    mock_user_auth = AsyncMock(spec=UserAuth)
    error_message = "Unexpected error"
    mock_user_auth.login = AsyncMock(side_effect=Exception(error_message))
    
    # Create AuthResource with mock UserAuth
    auth_resource = AuthResource(MagicMock())
    auth_resource.user_auth = mock_user_auth
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "password123"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "An unexpected error occurred during login" in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(username="testuser", password="password123")