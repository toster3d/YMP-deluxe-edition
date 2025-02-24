import logging
from typing import AsyncGenerator
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.password_validator import PasswordValidator
from services.user_auth_manager import RegistrationService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.mark.anyio
class TestRegistration:
    """Testy dla procesu rejestracji użytkownika."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession) -> AsyncGenerator[None, None]:
        """Setup dla testów."""
        self.password_validator = PasswordValidator()
        self.registration_service = RegistrationService(db_session)
        yield
        # Czyszczenie bazy po każdym teście
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()

    @pytest.mark.anyio
    async def test_valid_registration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ) -> None:
        """Test poprawnej rejestracji użytkownika."""
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass123!",
            "confirmation": "StrongPass123!"
        }

        response = await async_client.post(
            "/auth/register",
            json=registration_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"message": "Registration successful."}

        # Sprawdzenie, czy użytkownik został zapisany w bazie
        result = await db_session.execute(
            text("SELECT * FROM users WHERE user_name = :username"),
            {"username": "newuser"}
        )
        user = result.first()
        assert user is not None
        assert user.email == "newuser@example.com"

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "invalid_data,expected_error,expected_status",
        [
            (
                {
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "StrongPass123!",
                    "confirmation": "DifferentPass123!"
                },
                "Passwords do not match. Please ensure both passwords are identical.",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "email": "invalid-email",
                    "username": "newuser",
                    "password": "StrongPass123!",
                    "confirmation": "StrongPass123!"
                },
                "value is not a valid email address",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "email": "newuser@example.com",
                    "username": "nu",
                    "password": "StrongPass123!",
                    "confirmation": "StrongPass123!"
                },
                "String should have at least 3 characters",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "weak",
                    "confirmation": "weak"
                },
                "String should have at least 8 characters",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
        ]
    )
    async def test_invalid_registration(
        self,
        async_client: AsyncClient,
        invalid_data: dict[str, str],
        expected_error: str,
        expected_status: int
    ) -> None:
        """Test rejestracji z niepoprawnymi danymi."""
        response = await async_client.post(
            "/auth/register",
            json=invalid_data
        )

        assert response.status_code == expected_status
        response_json = response.json()
        
        # Dodajemy debug print dla łatwiejszej diagnostyki
        print(f"Response JSON: {response_json}")
        print(f"Expected error: {expected_error}")
        
        if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_messages = [error["msg"] for error in response_json["detail"]]
            assert any(expected_error in msg for msg in error_messages)

    @pytest.mark.anyio
    async def test_password_validation(
        self,
        async_client: AsyncClient
    ) -> None:
        """Test walidacji hasła podczas rejestracji."""
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "weakpassword",
            "confirmation": "weakpassword"
        }

        response = await async_client.post(
            "/auth/register",
            json=registration_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        error_messages = [error["msg"] for error in response_json["detail"]]
        assert any(
            "Password does not meet complexity requirements" in msg
            for msg in error_messages
        )
