import logging

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_logout_success(async_client: AsyncClient, auth_token: str) -> None:
    """Test poprawnego wylogowania."""  
    # Arrange
    # Przygotowujemy nagłówki autoryzacyjne
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Act
    logging.info(f"Sending logout request with token: {auth_token[:10]}...")
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK, f"Unexpected status code: {response.status_code}, response: {response.text}"
    assert response.json() == {"message": "Logout successful!"}


# @pytest.mark.asyncio
# async def test_logout_without_token(async_client: AsyncClient) -> None:
#     """Test próby wylogowania bez tokenu autoryzacyjnego."""
#     # Act
#     response = await async_client.post("/auth/logout")
    
#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     assert "Not authenticated" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_logout_with_invalid_token(async_client: AsyncClient) -> None:
#     """Test próby wylogowania z nieprawidłowym tokenem."""
#     # Arrange
#     headers = {"Authorization": "Bearer invalid_token"}
    
#     # Act
#     response = await async_client.post("/auth/logout", headers=headers)
    
#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     assert "Invalid token" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_logout_with_expired_token(async_client: AsyncClient) -> None:
#     """Test próby wylogowania z wygasłym tokenem."""
#     # Arrange
#     settings = get_settings()
    
#     # Tworzymy wygasły token
#     payload = {
#         "sub": "test@example.com",
#         "exp": 1000,  # Bardzo stara data wygaśnięcia
#         "iat": 900,
#         "jti": "test-jti"
#     }
#     expired_token = jwt.encode(
#         payload, 
#         settings.jwt_secret_key.get_secret_value(), 
#         algorithm=settings.jwt_algorithm
#     )
    
#     headers = {"Authorization": f"Bearer {expired_token}"}
    
#     # Act
#     response = await async_client.post("/auth/logout", headers=headers)
    
#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     assert "Token has expired" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_logout_token_without_jti(async_client: AsyncClient) -> None:
#     """Test próby wylogowania z tokenem bez identyfikatora JTI."""
#     # Arrange
#     settings = get_settings()
    
#     # Tworzymy token bez JTI
#     payload = {
#         "sub": "test@example.com",
#         "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
#         "iat": int(datetime.now(timezone.utc).timestamp())
#         # Brak JTI
#     }
#     token_without_jti = jwt.encode(
#         payload, 
#         settings.jwt_secret_key.get_secret_value(), 
#         algorithm=settings.jwt_algorithm
#     )
    
#     headers = {"Authorization": f"Bearer {token_without_jti}"}
    
#     # Act
#     response = await async_client.post("/auth/logout", headers=headers)
    
#     # Assert
#     assert response.status_code == status.HTTP_400_BAD_REQUEST
#     assert "Invalid token data: missing jti" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_logout_redis_error(async_client: AsyncClient, auth_token: str) -> None:
#     """Test obsługi błędu Redis podczas wylogowania."""
#     # Arrange
#     # Tworzymy mock dla TokenStorage, który rzuca wyjątek
#     mock_token_storage = AsyncMock(spec=RedisTokenStorage)
#     mock_token_storage.store.side_effect = TokenStorageError("Redis connection error")
    
#     # Używamy patch dla funkcji get_token_storage
#     with patch("src.dependencies.get_token_storage", return_value=mock_token_storage), \
#          patch("src.resources.auth_resource.get_token_storage", return_value=mock_token_storage):
        
#         # Przygotowujemy nagłówki autoryzacyjne
#         headers = {"Authorization": f"Bearer {auth_token}"}
        
#         # Act
#         response = await async_client.post("/auth/logout", headers=headers)
        
#         # Assert
#         assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
#         assert "An error occurred during logout" in response.json()["detail"]
#         assert "Redis connection error" in response.json()["detail"]
        
#         # Sprawdzamy, czy metoda store została wywołana
#         mock_token_storage.store.assert_called_once()


# @pytest.mark.asyncio
# async def test_logout_already_logged_out(async_client: AsyncClient, auth_token: str) -> None:
#     """Test próby wylogowania już wylogowanego użytkownika (token już na blackliście)."""
#     # Arrange
#     # Tworzymy mock dla TokenStorage, który zwraca True dla exists
#     mock_token_storage = AsyncMock(spec=RedisTokenStorage)
#     mock_token_storage.store.return_value = None
#     mock_token_storage.exists.return_value = True  # Token już istnieje na blackliście
    
#     # Używamy patch dla funkcji get_token_storage
#     with patch("src.dependencies.get_token_storage", return_value=mock_token_storage), \
#          patch("src.resources.auth_resource.get_token_storage", return_value=mock_token_storage), \
#          patch("src.jwt_utils.get_token_storage", return_value=mock_token_storage):
        
#         # Przygotowujemy nagłówki autoryzacyjne
#         headers = {"Authorization": f"Bearer {auth_token}"}
        
#         # Act
#         response = await async_client.post("/auth/logout", headers=headers)
        
#         # Assert
#         # Oczekujemy 401, ponieważ token jest już na blackliście
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#         assert "Token has been revoked" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_logout_multiple_times(async_client: AsyncClient, auth_token: str) -> None:
#     """Test wielokrotnego wylogowania z tym samym tokenem."""
#     # Arrange
#     # Tworzymy mock dla TokenStorage
#     mock_token_storage = AsyncMock(spec=RedisTokenStorage)
#     mock_token_storage.store.return_value = None
#     mock_token_storage.exists.side_effect = [False, True]  # Pierwsze wywołanie: token nie istnieje, drugie: token istnieje
    
#     # Używamy patch dla funkcji get_token_storage
#     with patch("src.dependencies.get_token_storage", return_value=mock_token_storage), \
#          patch("src.resources.auth_resource.get_token_storage", return_value=mock_token_storage), \
#          patch("src.jwt_utils.get_token_storage", return_value=mock_token_storage):
        
#         # Przygotowujemy nagłówki autoryzacyjne
#         headers = {"Authorization": f"Bearer {auth_token}"}
        
#         # Act - pierwsze wylogowanie
#         response1 = await async_client.post("/auth/logout", headers=headers)
        
#         # Assert - pierwsze wylogowanie powinno się udać
#         assert response1.status_code == status.HTTP_200_OK
#         assert response1.json() == {"message": "Logout successful!"}
        
#         # Act - drugie wylogowanie
#         response2 = await async_client.post("/auth/logout", headers=headers)
        
#         # Assert - drugie wylogowanie powinno zwrócić błąd
#         assert response2.status_code == status.HTTP_401_UNAUTHORIZED
#         assert "Token has been revoked" in response2.json()["detail"]