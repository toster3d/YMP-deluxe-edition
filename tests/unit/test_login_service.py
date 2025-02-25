import logging
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from models.recipes import User
from services.user_auth_manager import (
    InvalidCredentialsError,
    LoginService,
    MissingCredentialsError,
)

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_login_success(mock_db_session: AsyncSession) -> None:
    """Test successful login."""
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
    
    # Mockowanie check_password_hash i create_access_token
    with patch('services.user_auth_manager.check_password_hash', return_value=True), \
         patch('services.user_auth_manager.create_access_token', return_value="test_token"):
        
        login_service = LoginService(cast(AsyncSession, db_mock))
        
        # Act
        try:
            token = await login_service.login("testuser", "password")
            
            # Debug
            logger.debug(f"Token: {token}")
            
            # Assert
            assert token == "test_token"
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise

@pytest.mark.asyncio
async def test_login_missing_credentials() -> None:
    """Test login with missing credentials."""
    # Arrange
    db_mock = MagicMock(spec=AsyncSession)
    login_service = LoginService(cast(AsyncSession, db_mock))
    
    # Act & Assert
    with pytest.raises(MissingCredentialsError):
        await login_service.login("", "")

@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    """Test login with invalid credentials."""
    # Arrange
    hashed_password = generate_password_hash("password")
    user = User(
        user_name="testuser",
        hash=hashed_password,
        email="test@example.com"
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
    
    # Mockowanie check_password_hash aby zwracało False (niepoprawne hasło)
    with patch('services.user_auth_manager.check_password_hash', return_value=False):
        login_service = LoginService(cast(AsyncSession, db_mock))
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await login_service.login("testuser", "wrongpassword")