from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from src.services.user_auth_manager import (
    InvalidCredentialsError,
    LoginService,
    MissingCredentialsError,
    PasswordMismatchError,
    RegistrationError,
    RegistrationService,
    UserAuth,
)
from tests.test_models.models_db_test import TestUser


class TestUserAuth:
    """Tests for the main UserAuth class."""
    
    @pytest.fixture
    def mock_login_service(self) -> AsyncMock:
        login_service = AsyncMock()
        login_service.login.return_value = "test_token"
        return login_service
    
    @pytest.fixture
    def mock_registration_service(self) -> AsyncMock:
        registration_service = AsyncMock()
        registration_service.register.return_value = "Registration successful."
        return registration_service
    
    @pytest.fixture
    def mock_password_validator(self) -> MagicMock:
        validator = MagicMock()
        validator.validate.return_value = True
        return validator
    
    @pytest.fixture
    def user_auth(self, mock_db_session: AsyncMock, mock_login_service: AsyncMock, 
                 mock_registration_service: AsyncMock, mock_password_validator: MagicMock) -> UserAuth:
        with patch("src.services.user_auth_manager.LoginService", return_value=mock_login_service), \
             patch("src.services.user_auth_manager.RegistrationService", return_value=mock_registration_service), \
             patch("src.services.user_auth_manager.PasswordValidator", return_value=mock_password_validator):
            auth = UserAuth(mock_db_session)
            auth.login_service = mock_login_service
            auth.registration_service = mock_registration_service
            auth.password_validator = mock_password_validator
            return auth
    
    @pytest.mark.asyncio
    async def test_login_calls_login_service(self, user_auth: UserAuth) -> None:
        """Test if the login method calls login_service.login with correct arguments."""
        result = await user_auth.login("testuser", "password123")
        
        user_auth.login_service.login.assert_awaited_once_with("testuser", "password123")
        assert result == "test_token"
    
    @pytest.mark.asyncio
    async def test_register_calls_registration_service(self, user_auth: UserAuth) -> None:
        """Test if the register method calls registration_service.register with correct arguments."""
        result = await user_auth.register("testuser", "test@example.com", "password123", "password123")
        
        user_auth.registration_service.register.assert_awaited_once_with(  # type: ignore
            "testuser", "test@example.com", "password123", "password123"
        )
        assert result == "Registration successful."
    
    def test_validate_password_calls_validator(self, user_auth: UserAuth) -> None:
        """Test if the validate_password method calls password_validator.validate."""
        result = user_auth.validate_password("StrongPassword123!")
        
        user_auth.password_validator.validate.assert_called_once_with("StrongPassword123!") # type: ignore
        assert result is True


class TestLoginService:
    """Tests for the LoginService class."""
    
    @pytest.fixture
    def login_service(self, mock_db_session: AsyncMock) -> LoginService:
        with patch("src.services.user_auth_manager.User", TestUser):
            return LoginService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_login_with_missing_credentials(self, login_service: LoginService) -> None:
        """Test if login properly handles missing credentials."""
        missing_username_cases = [
            ("", "password"),
        ]
        
        missing_password_cases = [
            ("username", ""),
        ]
        
        for username, password in missing_username_cases + missing_password_cases:
            with pytest.raises(MissingCredentialsError):
                await login_service.login(username, password)
    
    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, login_service: LoginService, 
                                              mock_db_session: AsyncMock) -> None:
        """Test if login properly handles a nonexistent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with patch("src.services.user_auth_manager.select", return_value=select(TestUser)), \
             patch("src.services.user_auth_manager.check_password_hash", return_value=False):
            with pytest.raises(InvalidCredentialsError):
                await login_service.login("nonexistent", "password")
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_password(self, login_service: LoginService, 
                                             mock_db_session: AsyncMock) -> None:
        """Test if login properly handles an invalid password."""
        mock_user = MagicMock(spec=TestUser)
        mock_user.id = 1
        mock_user.user_name = "testuser"
        mock_user.hash = generate_password_hash("correctpassword")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with patch("src.services.user_auth_manager.select", return_value=select(TestUser)), \
             patch("src.services.user_auth_manager.check_password_hash") as mock_check_hash, \
             patch("src.services.user_auth_manager.create_access_token") as mock_create_token:
            
            mock_check_hash.return_value = False
            mock_create_token.return_value = "valid_token"
            
            with pytest.raises(InvalidCredentialsError):
                await login_service.login("testuser", "wrongpassword")
            
            mock_check_hash.assert_called_once_with(mock_user.hash, "wrongpassword")
            mock_create_token.assert_not_called()


class TestRegistrationService:
    """Tests for the RegistrationService class."""
    
    @pytest.fixture
    def registration_service(self, mock_db_session: AsyncMock) -> RegistrationService:
        with patch("src.services.user_auth_manager.User", TestUser):
            return RegistrationService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_register_with_mismatched_passwords(self, registration_service: RegistrationService) -> None:
        """Test if register properly handles mismatched passwords."""
        with pytest.raises(PasswordMismatchError):
            await registration_service.register(
                "testuser", "test@example.com", "password123", "differentpassword"
            )
    
    @pytest.mark.asyncio
    async def test_register_with_existing_username(self, registration_service: RegistrationService, 
                                                 mock_db_session: AsyncMock) -> None:
        """Test if register properly handles an existing username."""
        mock_user = MagicMock(spec=TestUser)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with patch("src.services.user_auth_manager.select", return_value=select(TestUser)):
            with pytest.raises(RegistrationError) as exc_info:
                await registration_service.register(
                    "existinguser", "test@example.com", "password123", "password123"
                )
            
            assert "Username already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_register_success(self, registration_service: RegistrationService, 
                                  mock_db_session: AsyncMock) -> None:
        """Test if register correctly registers a new user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        mock_user = MagicMock(spec=TestUser)
        with patch("src.services.user_auth_manager.select", return_value=select(TestUser)), \
             patch("src.services.user_auth_manager.User", return_value=mock_user):
            result = await registration_service.register(
                "newuser", "test@example.com", "password123", "password123"
            )
            
            assert result == "Registration successful."
            mock_db_session.add.assert_called_once_with(mock_user)
            mock_db_session.flush.assert_awaited_once()
            mock_db_session.commit.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_register_database_error(self, registration_service: RegistrationService, 
                                         mock_db_session: AsyncMock) -> None:
        """Test if register properly handles database errors."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        mock_db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        
        with patch("src.services.user_auth_manager.select", return_value=select(TestUser)):
            with pytest.raises(RegistrationError) as exc_info:
                await registration_service.register(
                    "newuser", "test@example.com", "password123", "password123"
                )
            
            assert "Registration failed" in str(exc_info.value)
            mock_db_session.rollback.assert_awaited_once()