from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.user_auth_manager import (
    InvalidCredentialsError,
    MissingCredentialsError,
    PasswordMismatchError,
    RegistrationError,
    RegistrationService,
    UserAuth,
)
from tests.test_models.models_db_test import TestUser


@pytest.fixture(scope="function")
async def mock_db_session() -> AsyncGenerator[AsyncMock, None]:
    db_mock = AsyncMock(spec=AsyncSession)
    yield db_mock

class TestUserAuth:
    
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
    def user_auth(
        self, 
        mock_db_session: AsyncMock, 
        mock_login_service: AsyncMock,
        mock_registration_service: AsyncMock, 
        mock_password_validator: MagicMock
    ) -> UserAuth:
        with patch("src.services.user_auth_manager.LoginService", return_value=mock_login_service), \
             patch("src.services.user_auth_manager.RegistrationService", return_value=mock_registration_service), \
             patch("src.services.user_auth_manager.PasswordValidator", return_value=mock_password_validator):
            auth = UserAuth(mock_db_session)
            auth.login_service = mock_login_service
            auth.registration_service = mock_registration_service
            auth.password_validator = mock_password_validator
            return auth

    class TestLogin:
        
        @pytest.mark.asyncio
        async def test_login_success(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.login_service, "login", return_value="test_token") as mock_login:
                result = await user_auth.login("testuser", "password123")
                mock_login.assert_awaited_once_with("testuser", "password123")
                assert result == "test_token"

        @pytest.mark.asyncio
        async def test_login_propagates_missing_credentials(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.login_service, "login", side_effect=MissingCredentialsError()) as mock_login:
                with pytest.raises(MissingCredentialsError):
                    await user_auth.login("", "")
                mock_login.assert_awaited_once_with("", "")

        @pytest.mark.asyncio
        async def test_login_propagates_invalid_credentials(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.login_service, "login", side_effect=InvalidCredentialsError()) as mock_login:
                with pytest.raises(InvalidCredentialsError):
                    await user_auth.login("testuser", "wrongpass")
                mock_login.assert_awaited_once_with("testuser", "wrongpass")

    class TestRegistration:
        
        @pytest.mark.asyncio
        async def test_register_success(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.registration_service, "register", 
                             return_value="Registration successful.") as mock_register:
                result = await user_auth.register(
                    "testuser", 
                    "test@example.com", 
                    "password123", 
                    "password123"
                )
                mock_register.assert_awaited_once_with(
                    "testuser", 
                    "test@example.com", 
                    "password123", 
                    "password123"
                )
                assert result == "Registration successful."

        @pytest.mark.asyncio
        async def test_register_propagates_password_mismatch(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.registration_service, "register", 
                             side_effect=PasswordMismatchError()) as mock_register:
                with pytest.raises(PasswordMismatchError):
                    await user_auth.register(
                        "testuser", 
                        "test@example.com", 
                        "password123", 
                        "different123"
                    )
                mock_register.assert_awaited_once_with(
                    "testuser",
                    "test@example.com",
                    "password123",
                    "different123"
                )

        @pytest.mark.asyncio
        async def test_register_propagates_registration_error(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.registration_service, "register", 
                             side_effect=RegistrationError("Username exists")) as mock_register:
                with pytest.raises(RegistrationError) as exc_info:
                    await user_auth.register(
                        "existing", 
                        "test@example.com", 
                        "password123", 
                        "password123"
                    )
                mock_register.assert_awaited_once_with(
                    "existing",
                    "test@example.com",
                    "password123",
                    "password123"
                )
                assert "Username exists" in str(exc_info.value)

    class TestPasswordValidation:
        
        def test_validate_password_success(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.password_validator, "validate", return_value=True) as mock_validate:
                result = user_auth.validate_password("StrongPassword123!")
                mock_validate.assert_called_once_with("StrongPassword123!")
                assert result is True

        def test_validate_password_failure(self, user_auth: UserAuth) -> None:
            with patch.object(user_auth.password_validator, "validate", return_value=False) as mock_validate:
                result = user_auth.validate_password("weak")
                mock_validate.assert_called_once_with("weak")
                assert result is False


class TestRegistrationService:
    
    @pytest.fixture
    def registration_service(self, mock_db_session: AsyncMock) -> RegistrationService:
        with patch("src.services.user_auth_manager.User", TestUser):
            return RegistrationService(mock_db_session)

    class TestRegister:
        
        @pytest.mark.asyncio
        async def test_register_success(
            self, 
            registration_service: RegistrationService, 
            mock_db_session: AsyncMock
        ) -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            
            with patch.object(mock_db_session, "execute", return_value=mock_result), \
                 patch.object(mock_db_session, "add") as mock_add, \
                 patch.object(mock_db_session, "flush") as mock_flush, \
                 patch.object(mock_db_session, "commit") as mock_commit:
                
                result = await registration_service.register(
                    "newuser", 
                    "test@example.com", 
                    "password123", 
                    "password123"
                )
                
                assert result == "Registration successful."
                mock_add.assert_called_once()
                mock_flush.assert_awaited_once()
                mock_commit.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_register_password_mismatch(
            self, 
            registration_service: RegistrationService
        ) -> None:
            with pytest.raises(PasswordMismatchError):
                await registration_service.register(
                    "testuser", 
                    "test@example.com", 
                    "password123", 
                    "different123"
                )

        @pytest.mark.asyncio
        async def test_register_existing_username(
            self, 
            registration_service: RegistrationService, 
            mock_db_session: AsyncMock
        ) -> None:
            mock_result = MagicMock()
            existing_user = TestUser(
                user_name="existing",
                email="existing@example.com",
                hash="hash"
            )
            mock_result.scalar_one_or_none.return_value = existing_user
            
            with patch.object(mock_db_session, "execute", return_value=mock_result):
                with pytest.raises(RegistrationError) as exc_info:
                    await registration_service.register(
                        "existing", 
                        "test@example.com", 
                        "password123", 
                        "password123"
                    )
                assert "Username already exists" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_register_database_error(
            self, 
            registration_service: RegistrationService, 
            mock_db_session: AsyncMock
        ) -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db_error = Exception("Database error")
            
            with patch.object(mock_db_session, "execute", return_value=mock_result), \
                 patch.object(mock_db_session, "commit", side_effect=db_error), \
                 patch.object(mock_db_session, "rollback") as mock_rollback:
                
                with pytest.raises(RegistrationError) as exc_info:
                    await registration_service.register(
                        "newuser", 
                        "test@example.com", 
                        "password123", 
                        "password123"
                    )
                assert "Registration failed" in str(exc_info.value)
                mock_rollback.assert_awaited_once()