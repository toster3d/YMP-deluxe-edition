import asyncio
from typing import AsyncGenerator, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from resources.auth_resource import AuthResource
from resources.pydantic_schemas import TokenResponse
from services.user_auth_manager import (
    InvalidCredentialsError,
    TokenError,
    UserAuth,
)


@pytest.fixture
async def auth_resource(db_session: AsyncSession) -> AsyncGenerator[AuthResource, None]:
    resource = AuthResource(db_session)
    yield resource

@pytest.fixture
def mock_user_auth() -> AsyncMock:
    return AsyncMock(spec=UserAuth)

@pytest.fixture
def form_data() -> MagicMock:
    form = MagicMock(spec=OAuth2PasswordRequestForm)
    form.username = "testuser"
    form.password = "password123"
    return form

@pytest.mark.asyncio
async def test_login_with_form_success(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    mock_user_auth.login = AsyncMock(return_value="test_token")
    auth_resource.user_auth = mock_user_auth
    
    result = await auth_resource.login_with_form(form_data)
    
    assert result.access_token == "test_token"
    assert result.token_type == "bearer"
    mock_user_auth.login.assert_called_once_with(
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_login_with_form_missing_credentials(
    auth_resource: AuthResource,
    form_data: MagicMock
) -> None:
    form_data.username = ""
    form_data.password = ""
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Missing credentials" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_with_form_invalid_credentials(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    mock_user_auth.login = AsyncMock(side_effect=InvalidCredentialsError())
    auth_resource.user_auth = mock_user_auth
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid username or password" in str(exc_info.value.detail)
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    mock_user_auth.login.assert_called_once_with(
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_login_with_form_token_error(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    error_message = "Token generation failed"
    mock_user_auth.login = AsyncMock(side_effect=TokenError(error_message))
    auth_resource.user_auth = mock_user_auth
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error_message in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_login_with_form_unexpected_error(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    error_message = "Unexpected error"
    mock_user_auth.login = AsyncMock(side_effect=Exception(error_message))
    auth_resource.user_auth = mock_user_auth
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "An unexpected error occurred during login" in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_login_with_form_special_characters(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    form_data.username = "test@user!123"
    form_data.password = "pass@word!123"
    mock_user_auth.login = AsyncMock(return_value="test_token")
    auth_resource.user_auth = mock_user_auth
    
    result = await auth_resource.login_with_form(form_data)
    
    assert result.access_token == "test_token"
    assert result.token_type == "bearer"
    mock_user_auth.login.assert_called_once_with(
        username="test@user!123",
        password="pass@word!123"
    )

@pytest.mark.asyncio
async def test_login_with_form_none_values(
    auth_resource: AuthResource,
    form_data: MagicMock
) -> None:
    form_data.username = None
    form_data.password = None
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Missing credentials" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_with_form_long_credentials(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    form_data.username = "a" * 1000
    form_data.password = "b" * 1000
    mock_user_auth.login = AsyncMock(return_value="test_token")
    auth_resource.user_auth = mock_user_auth
    
    result = await auth_resource.login_with_form(form_data)
    
    assert result.access_token == "test_token"
    assert result.token_type == "bearer"
    mock_user_auth.login.assert_called_once_with(
        username="a" * 1000,
        password="b" * 1000
    )

@pytest.mark.asyncio
async def test_login_with_form_database_error(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    mock_user_auth.login = AsyncMock(side_effect=Exception("Database connection error"))
    auth_resource.user_auth = mock_user_auth
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_resource.login_with_form(form_data)
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "An unexpected error occurred during login" in str(exc_info.value.detail)
    mock_user_auth.login.assert_called_once_with(
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_login_with_form_concurrent_requests(
    auth_resource: AuthResource,
    mock_user_auth: AsyncMock,
    form_data: MagicMock
) -> None:
    mock_user_auth.login = AsyncMock(return_value="test_token")
    auth_resource.user_auth = mock_user_auth
    
    results: Tuple[TokenResponse, TokenResponse] = await asyncio.gather(
        auth_resource.login_with_form(form_data),
        auth_resource.login_with_form(form_data)
    )
    
    assert all(result.access_token == "test_token" for result in results)
    assert all(result.token_type == "bearer" for result in results)
    assert mock_user_auth.login.call_count == 2
    mock_user_auth.login.assert_any_call(
        username="testuser",
        password="password123"
    )