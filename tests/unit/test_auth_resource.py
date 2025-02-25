import logging
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.recipes import User
from resources.auth_resource import AuthResource
from resources.pydantic_schemas import TokenResponse
from services.user_auth_manager import UserAuth

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login_with_form_success(mock_db_session: AsyncSession) -> None:
    """Test successful login with form data."""
    # Arrange
    hashed_password = generate_password_hash("password")
    user = User(
        user_name="testuser",
        hash=hashed_password,
        email="test@example.com",
        id=1  # Dodaj ID, które jest potrzebne do generowania tokenu
    )
    
    # Tworzymy nowy mock zamiast modyfikować istniejący
    db_mock = MagicMock(spec=AsyncSession)
    
    # Poprawne mockowanie dla SQLAlchemy 2.0 zgodne z typowaniem
    result_mock = MagicMock()
    # Kluczowa zmiana: zwracamy obiekt User bezpośrednio, nie coroutine
    result_mock.scalar_one_or_none.return_value = user
    
    execute_mock = AsyncMock()
    execute_mock.return_value = result_mock
    db_mock.execute = execute_mock
    
    # Mockowanie UserAuth.login
    login_mock = AsyncMock()
    login_mock.return_value = "test_token"
    
    with patch.object(UserAuth, 'login', new=login_mock):
        auth_resource = AuthResource(cast(AsyncSession, db_mock))
        form_data = OAuth2PasswordRequestForm(
            username="testuser",
            password="password",
            scope="",
            client_id=None,
            client_secret=None
        )
        
        # Act
        try:
            response = await auth_resource.login_with_form(form_data)
            
            # Debug
            logger.debug(f"Response: {response}")
            
            # Assert
            assert isinstance(response, TokenResponse)
            assert response.access_token == "test_token"
            assert response.token_type == "bearer"
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise

@pytest.mark.asyncio
async def test_login_with_form_missing_credentials() -> None:
    """Test login with missing credentials."""
    # Arrange
    db_mock = MagicMock(spec=AsyncSession)
    auth_resource = AuthResource(cast(AsyncSession, db_mock))
    form_data = OAuth2PasswordRequestForm(
        username="",
        password="",
        scope="",
        client_id=None,
        client_secret=None
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    assert exc_info.value.status_code == 400 