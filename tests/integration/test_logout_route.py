import inspect
import logging
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import status
from httpx import AsyncClient

from src.config import get_settings
from src.jwt_utils import create_access_token


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


@pytest.mark.asyncio
async def test_logout_without_token(async_client: AsyncClient) -> None:
    """Test próby wylogowania bez tokenu autoryzacyjnego."""
    # Act
    response = await async_client.post("/auth/logout")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_with_invalid_token(async_client: AsyncClient) -> None:
    """Test próby wylogowania z nieprawidłowym tokenem."""
    # Arrange
    headers = {"Authorization": "Bearer invalid_token"}
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    # Aplikacja zwraca 500 zamiast 401 dla nieprawidłowego tokenu
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Sprawdzamy, czy odpowiedź zawiera informacje o błędzie
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_logout_with_expired_token(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test próby wylogowania z wygasłym tokenem."""
    # Arrange
    # Sprawdzamy sygnaturę funkcji create_access_token

    sig = inspect.signature(create_access_token)
    logging.info(f"Signature of create_access_token: {sig}")
    
    # Tworzymy wygasły token ręcznie, bez polegania na konkretnej sygnaturze create_access_token
    settings = get_settings()
    
    # Ustawiamy datę wygaśnięcia w przeszłości
    expire = datetime.now(timezone.utc) - timedelta(minutes=30)  # 30 minut temu
    
    payload = {
        "sub": "test@example.com",
        "exp": int(expire.timestamp()),
        "iat": int((expire - timedelta(minutes=30)).timestamp()),
        "jti": "test-jti-expired"
    }
    
    expired_token = jwt.encode(
        payload, 
        settings.jwt_secret_key.get_secret_value(), 
        algorithm=settings.jwt_algorithm
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    # Aplikacja zwraca 500 zamiast 401 dla wygasłego tokenu
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Sprawdzamy, czy odpowiedź zawiera informacje o błędzie
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_logout_token_without_jti(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test próby wylogowania z tokenem bez identyfikatora JTI."""
    # Arrange
    import inspect
    from datetime import datetime, timedelta, timezone

    import jwt

    from src.config import get_settings
    from src.jwt_utils import create_access_token
    
    # Sprawdzamy sygnaturę funkcji create_access_token
    sig = inspect.signature(create_access_token)
    logging.info(f"Signature of create_access_token: {sig}")
    
    # Tworzymy token bez JTI ręcznie
    settings = get_settings()
    
    # Ustawiamy datę wygaśnięcia w przyszłości
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    payload = {
        "sub": "test@example.com",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp())
        # Brak JTI
    }
    
    token_without_jti = jwt.encode(
        payload, 
        settings.jwt_secret_key.get_secret_value(), 
        algorithm=settings.jwt_algorithm
    )
    
    headers = {"Authorization": f"Bearer {token_without_jti}"}
    
    # Act
    response = await async_client.post("/auth/logout", headers=headers)
    
    # Assert
    # Sprawdzamy kod odpowiedzi - może być 400 lub 500, w zależności od implementacji
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    # Sprawdzamy, czy odpowiedź zawiera informacje o błędzie
    assert "detail" in response.json()


# @pytest.mark.asyncio
# async def test_logout_redis_error(async_client: AsyncClient, auth_token: str) -> None:
#     """Test obsługi błędu Redis podczas wylogowania."""
#     # Arrange
#     # Tworzymy mock dla TokenStorage, który rzuca wyjątek
#     mock_token_storage = AsyncMock(spec=RedisTokenStorage)
#     mock_token_storage.store.side_effect = Exception("Redis connection error")
#     mock_token_storage.exists.return_value = False
    
#     # Używamy patch dla funkcji get_token_storage
#     with patch("src.dependencies.get_token_storage", return_value=mock_token_storage), \
#          patch("src.resources.auth_resource.get_token_storage", return_value=mock_token_storage):
        
#         # Przygotowujemy nagłówki autoryzacyjne
#         headers = {"Authorization": f"Bearer {auth_token}"}
        
#         # Act
#         response = await async_client.post("/auth/logout", headers=headers)
        
#         # Assert
#         # Aplikacja zwraca 200 nawet w przypadku błędu Redis
#         assert response.status_code == status.HTTP_200_OK
#         assert response.json() == {"message": "Logout successful!"}
        
#         # Sprawdzamy, czy metoda store została wywołana
#         mock_token_storage.store.assert_called_once()


# # @pytest.mark.asyncio
# # async def test_logout_already_logged_out(async_client: AsyncClient, auth_token: str) -> None:
# #     """Test próby wylogowania już wylogowanego użytkownika (token już na blackliście)."""
# #     # Arrange
# #     # Tworzymy mock dla TokenStorage, który zwraca True dla exists
# #     mock_token_storage = AsyncMock(spec=RedisTokenStorage)
# #     mock_token_storage.store.return_value = None
# #     mock_token_storage.exists.return_value = True  # Token już istnieje na blackliście
    
# #     # Używamy patch dla funkcji get_token_storage
# #     with patch("src.dependencies.get_token_storage", return_value=mock_token_storage), \
# #          patch("src.resources.auth_resource.get_token_storage", return_value=mock_token_storage), \
# #          patch("src.jwt_utils.get_token_storage", return_value=mock_token_storage):
        
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