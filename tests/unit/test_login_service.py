import logging

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_models.models_db_test import TestUser

from services.user_auth_manager import (
    InvalidCredentialsError,
    MissingCredentialsError,
    PasswordMismatchError,
    RegistrationError,
    UserAuth,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestUserAuth:
    """Test suite for UserAuth service."""

    @pytest.fixture
    def user_auth(self, db_session: AsyncSession) -> UserAuth:
        """Fixture providing UserAuth instance."""
        return UserAuth(db_session)

    @pytest.fixture
    def test_user_data(self) -> dict[str, str]:
        """Fixture providing test user data."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!",
            "confirmation": "Test123!"
        }

    @pytest.mark.asyncio
    async def test_login_success(
        self, async_client: AsyncClient, create_test_user: TestUser
    ) -> None:
        """Test successful login."""
        response = await async_client.post(
            "/auth/login",
            data={
                "username": create_test_user.user_name,
                "password": "Test123!"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, user_auth: UserAuth) -> None:
        """Test login with missing credentials."""
        with pytest.raises(MissingCredentialsError):
            await user_auth.login("", "")

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, user_auth: UserAuth, create_test_user: TestUser
    ) -> None:
        """Test login with invalid credentials."""
        with pytest.raises(InvalidCredentialsError):
            await user_auth.login(create_test_user.user_name, "WrongPassword123!")

    @pytest.mark.asyncio
    async def test_login_with_form_invalid_credentials(
        self, async_client: AsyncClient
    ) -> None:
        """Test login with invalid credentials via form."""
        response = await async_client.post(
            "/auth/login",
            data={"username": "wronguser", "password": "WrongPassword123!"}
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_register_success(
        self, user_auth: UserAuth, test_user_data: dict[str, str]
    ) -> None:
        """Test successful user registration."""
        result = await user_auth.register(
            test_user_data["username"],
            test_user_data["email"],
            test_user_data["password"],
            test_user_data["confirmation"]
        )
        assert "success" in result.lower()

    @pytest.mark.asyncio
    async def test_register_password_mismatch(
        self, user_auth: UserAuth, test_user_data: dict[str, str]
    ) -> None:
        """Test registration with mismatched passwords."""
        with pytest.raises(PasswordMismatchError):
            await user_auth.register(
                test_user_data["username"],
                test_user_data["email"],
                test_user_data["password"],
                "DifferentPassword123!"
            )

    @pytest.mark.asyncio
    async def test_register_existing_user(
        self, user_auth: UserAuth, create_test_user: TestUser
    ) -> None:
        """Test registration with existing username."""
        with pytest.raises(RegistrationError):
            await user_auth.register(
                create_test_user.user_name,
                "new@example.com",
                "Test123!",
                "Test123!"
            )

    @pytest.mark.asyncio
    async def test_login_with_empty_strings(self, user_auth: UserAuth) -> None:
        """Test login with empty strings."""
        with pytest.raises(MissingCredentialsError):
            await user_auth.login("", "")

    @pytest.mark.asyncio
    async def test_login_with_whitespace(
        self, user_auth: UserAuth, create_test_user: TestUser
    ) -> None:
        """Test login with whitespace in credentials."""
        with pytest.raises(InvalidCredentialsError):
            await user_auth.login(
                " " + create_test_user.user_name + " ",
                " Test123! "
            )

    @pytest.mark.asyncio
    async def test_login_with_none_values(self, user_auth: UserAuth) -> None:
        """Test login with None values."""
        with pytest.raises(MissingCredentialsError):
            await user_auth.login(None, None) # type: ignore

    @pytest.mark.asyncio
    async def test_login_with_long_credentials(
        self, user_auth: UserAuth, create_test_user: TestUser
    ) -> None:
        """Test login with very long credentials."""
        with pytest.raises(InvalidCredentialsError):
            await user_auth.login(
                create_test_user.user_name + "x" * 1000,
                "Test123!" + "x" * 1000
            )

    @pytest.mark.asyncio
    async def test_login_with_special_characters(
        self, user_auth: UserAuth, create_test_user: TestUser
    ) -> None:
        """Test login with special characters in credentials."""
        with pytest.raises(InvalidCredentialsError):
            await user_auth.login(
                create_test_user.user_name + "!@#$%^&*()",
                "Test123!"
            )