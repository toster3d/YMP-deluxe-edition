# from datetime import datetime, timezone

# import jwt
# import pytest
# from fastapi import status
# from fastapi.security import OAuth2PasswordRequestForm
# from httpx import AsyncClient

# from resources.pydantic_schemas import RegisterSchema


# # Mocki pozostają takie same
# class MockAuthResource:
#     async def login_with_form(self, form_data: OAuth2PasswordRequestForm) -> dict[str, str]:
#         if form_data.username == "test@example.com" and form_data.password == "testpass":
#             return {
#                 "access_token": "valid_token",
#                 "token_type": "bearer"
#             }
#         raise Exception("Invalid credentials")

# class MockRegisterResource:
#     async def post(self, register_data: RegisterSchema) -> dict[str, str]:
#         if register_data.email == "exists@example.com":
#             raise Exception("User already exists")
#         return {"message": "User registered successfully"}

# class MockLogoutResource:
#     async def post(self, token: str) -> dict[str, str]:
#         if token == "invalid_token":
#             raise Exception("Invalid token")
#         return {"message": "Logged out successfully"}

# @pytest.fixture
# def mock_auth_resource() -> MockAuthResource:
#     return MockAuthResource()

# @pytest.fixture
# def mock_register_resource() -> MockRegisterResource:
#     return MockRegisterResource()

# @pytest.fixture
# def mock_logout_resource() -> MockLogoutResource:
#     return MockLogoutResource()

# # Testy jako funkcje modułowe
# @pytest.mark.asyncio
# async def test_login_success(async_client: AsyncClient) -> None:
#     """Test successful login."""
#     response = await async_client.post(
#         "/auth/login",
#         data={
#             "username": "test@example.com",
#             "password": "testpass"
#         },
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
    
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert "access_token" in data
#     assert data["token_type"] == "bearer"

# @pytest.mark.asyncio
# async def test_login_invalid_credentials(async_client: AsyncClient) -> None:
#     """Test login with invalid credentials."""
#     response = await async_client.post(
#         "/auth/login",
#         data={
#             "username": "wrong@example.com",
#             "password": "wrongpass"
#         },
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
    
#     assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

# @pytest.mark.asyncio
# async def test_register_success(async_client: AsyncClient) -> None:
#     """Test successful user registration."""
#     response = await async_client.post(
#         "/auth/register",
#         json={
#             "email": "new@example.com",
#             "password": "newpass123",
#             "confirm_password": "newpass123"
#         }
#     )
    
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
#     assert data["message"] == "User registered successfully"

# @pytest.mark.asyncio
# async def test_register_existing_user(async_client: AsyncClient) -> None:
#     """Test registration with existing email."""
#     response = await async_client.post(
#         "/auth/register",
#         json={
#             "email": "exists@example.com",
#             "password": "pass123",
#             "confirm_password": "pass123"
#         }
#     )
    
#     assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

# @pytest.mark.asyncio
# async def test_register_password_mismatch(async_client: AsyncClient) -> None:
#     """Test registration with mismatched passwords."""
#     response = await async_client.post(
#         "/auth/register",
#         json={
#             "email": "new@example.com",
#             "password": "pass123",
#             "confirm_password": "different123"
#         }
#     )
    
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# @pytest.mark.asyncio
# async def test_logout_success(async_client: AsyncClient, auth_headers: dict[str, str]) -> None:
#     """Test successful logout."""
#     response = await async_client.post(
#         "/auth/logout",
#         headers=auth_headers
#     )
    
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["message"] == "Logged out successfully"

# @pytest.mark.asyncio
# async def test_logout_invalid_token(async_client: AsyncClient) -> None:
#     """Test logout with invalid token."""
#     response = await async_client.post(
#         "/auth/logout",
#         headers={"Authorization": "Bearer invalid_token"}
#     )
    
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED

# @pytest.mark.asyncio
# async def test_verify_token_success(async_client: AsyncClient, auth_headers: dict[str, str]) -> None:
#     """Test successful token verification."""
#     response = await async_client.get(
#         "/protected-route",
#         headers=auth_headers
#     )
    
#     assert response.status_code != status.HTTP_401_UNAUTHORIZED

# @pytest.mark.asyncio
# async def test_verify_token_expired(async_client: AsyncClient) -> None:
#     """Test expired token verification."""
#     expired_token = jwt.encode(
#         {
#             "sub": "test@example.com",
#             "exp": datetime.now(timezone.utc)
#         },
#         "secret_key",
#         algorithm="HS256"
#     )
    
#     response = await async_client.get(
#         "/protected-route",
#         headers={"Authorization": f"Bearer {expired_token.decode()}"}
#     )
    
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED

# @pytest.mark.asyncio
# async def test_login_invalid_content_type(async_client: AsyncClient) -> None:
#     """Test login with invalid content type."""
#     response = await async_client.post(
#         "/auth/login",
#         json={
#             "username": "test@example.com",
#             "password": "testpass"
#         }
#     )
    
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY