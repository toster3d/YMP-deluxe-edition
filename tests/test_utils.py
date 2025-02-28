# """Narzędzia pomocnicze dla testów."""
# import logging
# from typing import Any, AsyncGenerator, Callable, TypeVar
# from unittest.mock import AsyncMock

# import pytest_asyncio
# from fastapi import FastAPI
# from httpx import ASGITransport, AsyncClient

# from src.jwt_utils import create_access_token
# from tests.settings import get_test_settings

# settings = get_test_settings()
# logger = logging.getLogger(__name__)

# T = TypeVar('T')

# def async_mock_factory(return_value: T) -> AsyncMock:
#     """Tworzy AsyncMock z określoną wartością zwracaną."""
#     mock = AsyncMock()
#     mock.return_value = return_value
#     return mock

# @pytest_asyncio.fixture(scope="session")
# async def test_app() -> AsyncGenerator[FastAPI, None]:
#     """Tworzy testową aplikację FastAPI."""
#     from src.app import create_application
    
#     app = create_application()
#     yield app

# @pytest_asyncio.fixture(scope="session")
# async def test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
#     """Tworzy klienta testowego dla aplikacji FastAPI."""
#     async with AsyncClient(
#         transport=ASGITransport(app=test_app),
#         base_url="http://test",
#         follow_redirects=True
#     ) as client:
#         yield client

# @pytest_asyncio.fixture(scope="session")
# async def test_token() -> str:
#     """Tworzy token JWT dla testów."""
#     return create_access_token(
#         user_id=1,
#         username=settings.TEST_USER_NAME
#     )

# @pytest_asyncio.fixture(scope="session")
# async def test_headers(test_token: str) -> dict[str, str]:
#     """Tworzy nagłówki autoryzacyjne dla testów."""
#     return {"Authorization": f"Bearer {test_token}"}

# # Funkcja pomocnicza do obsługi wyjątków w testach
# async def handle_test_exceptions(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
#     """Obsługuje wyjątki w testach i zapisuje je do logów."""
#     try:
#         return await func(*args, **kwargs)
#     except Exception as e:
#         logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
#         raise 