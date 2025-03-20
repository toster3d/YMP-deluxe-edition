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


class TestRegistration:
    """Tests for the user registration process."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession) -> AsyncGenerator[None, None]:
        """Setup for tests."""
        self.password_validator = PasswordValidator()
        self.registration_service = RegistrationService(db_session)
        yield
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_valid_registration(self, async_client: AsyncClient) -> None:
        """Test for successful user registration."""
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
        data = response.json()
        assert "message" in data
        assert "Registration successful." in data["message"]

    @pytest.mark.asyncio
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
        """Test registration with invalid data."""
        response = await async_client.post(
            "/auth/register",
            json=invalid_data
        )

        assert response.status_code == expected_status
        response_json = response.json()

        print(f"Response JSON: {response_json}")
        print(f"Expected error: {expected_error}")

        if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_messages = [error["msg"] for error in response_json["detail"]]
            assert any(expected_error in msg for msg in error_messages)

    @pytest.mark.asyncio
    async def test_password_validation(
        self,
        async_client: AsyncClient
    ) -> None:
        """Test password validation during registration."""
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
        
        print(f"Response JSON: {response_json}")
        
        if "detail" in response_json and isinstance(response_json["detail"], list):
            error_messages = [error["msg"] for error in response_json["detail"]]
            assert any(
                "Password does not meet complexity requirements" in msg
                for msg in error_messages
            )
        elif "detail" in response_json and isinstance(response_json["detail"], dict):
            assert "Password does not meet complexity requirements" in response_json["detail"].get("msg", "")
        elif "message" in response_json:
            assert "Password does not meet complexity requirements" in response_json["message"]
        else:
            assert False, f"Unexpected response format: {response_json}"
