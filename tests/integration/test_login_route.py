import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from routes import router
from services.user_auth_manager import InvalidCredentialsError, MissingCredentialsError
from tests.test_models.models_db_test import TestUser

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.mark.asyncio
class TestLoginRoute:
    """Tests for /auth/login route."""

    async def test_login_success(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test successful login."""
        try:
            result = await db_session.execute(select(TestUser).filter_by(user_name="testuser"))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.debug(f"User testuser already exists with ID: {existing_user.id}")
                user = existing_user
            else:
                hashed_password = generate_password_hash("password")
                user = TestUser(
                    user_name="testuser",
                    hash=hashed_password,
                    email="test@example.com"
                )
                db_session.add(user)
                await db_session.commit()
                await db_session.refresh(user)
                logger.debug(f"Added user: {user.user_name} with ID: {user.id}")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/auth/login",
                    data={"username": "testuser", "password": "password"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response body: {response.text}")
                
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise

    async def test_login_invalid_credentials(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test login with invalid credentials."""
        try:
            result = await db_session.execute(select(TestUser).filter_by(user_name="testuser"))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                hashed_password = generate_password_hash("password")
                user = TestUser(
                    user_name="testuser",
                    hash=hashed_password,
                    email="test@example.com"
                )
                db_session.add(user)
                await db_session.commit()
                await db_session.refresh(user)
                logger.debug(f"Added user: {user.user_name} with ID: {user.id}")
            else:
                logger.debug(f"User testuser already exists with ID: {existing_user.id}")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/auth/login",
                    data={"username": "testuser", "password": "wrongpassword"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response body: {response.text}")
                
                assert response.status_code == 401
                data = response.json()
                assert "detail" in data
                assert data["detail"] == "Invalid username or password."
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise

    async def test_login_http_exception_passthrough(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test that HTTP exceptions are passed through without modification."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("src.resources.auth_resource.AuthResource.login_with_form") as mock_login:
                mock_login.side_effect = InvalidCredentialsError()
                
                response = await client.post(
                    "/auth/login",
                    data={"username": "testuser", "password": "password"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                assert response.status_code == 401
                assert response.json()["detail"] == "Invalid username or password."

    async def test_login_missing_credentials(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test login with missing credentials."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                data={"username": "", "password": ""},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            assert response.status_code == 400
            error_detail = response.json()["detail"]
            assert "Missing credentials" in error_detail

    async def test_login_invalid_credentials_error(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test that InvalidCredentialsError is properly handled."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("src.services.user_auth_manager.UserAuth.login") as mock_login:
                mock_login.side_effect = InvalidCredentialsError()
                
                response = await client.post(
                    "/auth/login",
                    data={"username": "testuser", "password": "password"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                assert response.status_code == 401
                data = response.json()
                assert "detail" in data
                assert "Invalid username or password" in data["detail"]
                assert response.headers.get("www-authenticate") == "Bearer"

    async def test_login_missing_credentials_error(self, app: FastAPI, db_session: AsyncSession) -> None:
        """Test that MissingCredentialsError is properly handled."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("src.services.user_auth_manager.UserAuth.login") as mock_login:
                mock_login.side_effect = MissingCredentialsError()
                
                response = await client.post(
                    "/auth/login",
                    data={"username": "testuser", "password": "password"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                assert response.status_code == 401
                data = response.json()
                assert "detail" in data
                assert "Invalid username or password" in data["detail"] 