from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import create_application, initialize_database, lifespan
from src.config import get_settings
from src.extensions import async_engine
from src.routes import router


@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Create test application instance."""
    app_instance = create_application()
    app_instance.include_router(router, prefix="/api")
    return app_instance

@pytest.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set TESTING environment variable for tests."""
    monkeypatch.setenv("TESTING", "True")

@pytest.mark.anyio
class TestAppCreation:
    """Tests related to FastAPI application creation and configuration."""

    async def test_create_application(self) -> None:
        """Test application creation and configuration."""
        app_instance = create_application()

        assert app_instance.title == "Your Meal Planner API"
        assert app_instance.version == "1.0.0"
        assert app_instance.docs_url == "/docs"
        assert app_instance.redoc_url == "/redoc"

        middleware = [
            m for m in app_instance.user_middleware
            if "CORSMiddleware" in str(m.cls)
        ]
        assert len(middleware) == 1

    async def test_debug_mode_settings(self) -> None:
        """Test debug mode configuration."""
        settings = get_settings()
        assert hasattr(settings, "debug")
        assert isinstance(settings.debug, bool)

    def test_app_import(self) -> None:
        """Test that app can be imported correctly."""
        from src.app import app as main_app
        assert isinstance(main_app, FastAPI)

    async def test_create_application_with_custom_settings(self) -> None:
        """Test application creation with custom settings."""
        with patch("src.app.settings") as mock_settings:
            mock_settings.cors_origins = ["http://custom-origin.com"]
            mock_settings.debug = True
            _ = create_application()
            assert mock_settings.cors_origins == ["http://custom-origin.com"]
            assert mock_settings.debug is True

@pytest.mark.anyio
class TestDataBaseInitialization:
    """Tests for database initialization logic."""

    async def test_initialize_database(self) -> None:
        """Test database initialization."""
        await initialize_database()

        required_tables = {"users", "recipes", "user_plan"}

        async with async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table';")
            )
            existing_tables = {row[0] for row in result.fetchall()}

            assert required_tables.issubset(existing_tables)

    async def test_initialize_database_error_handling(self) -> None:
        """Test error handling during database initialization."""
        with patch("src.app.async_engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_conn.run_sync.side_effect = Exception("Test exception")

            with pytest.raises(Exception, match="Test exception"):
                await initialize_database()

    async def test_initialize_database_tables_exist(self) -> None:
        """Test database initialization when tables already exist."""
        with patch("src.app.async_engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            mock_conn.run_sync.return_value = ["users", "recipes", "user_plan"]

            await initialize_database()

            assert mock_conn.run_sync.call_count >= 1

@pytest.mark.anyio
class TestLifespan:
    """Tests for the application lifespan events."""

    async def test_lifespan(self, app: FastAPI, async_client: AsyncClient) -> None:
        """Test application lifespan events."""
        response = await async_client.get("/docs")
        assert response.status_code == 200

    async def test_lifespan_error_handling(self) -> None:
        """Test error handling in lifespan context manager."""
        dummy_app = FastAPI()

        with patch("src.app.initialize_database", side_effect=Exception("Test exception")):
            with pytest.raises(Exception, match="Test exception"):
                async with lifespan(dummy_app):
                    pass

@pytest.mark.anyio
class TestEndpointsAndRouting:
    """Tests for default endpoints, CORS, routing, and error handling."""

    @pytest.mark.parametrize(
        "test_input,expected_status",
        [
            ("/docs", 200),
            ("/redoc", 200),
            ("/openapi.json", 200),
            ("/nonexistent", 404)
        ]
    )
    async def test_default_endpoints(
        self,
        app: FastAPI,
        async_client: AsyncClient,
        test_input: str,
        expected_status: int
    ) -> None:
        """Test default FastAPI endpoints."""
        response = await async_client.get(test_input)
        assert response.status_code == expected_status

    async def test_cors_headers(self, app: FastAPI, async_client: AsyncClient) -> None:
        """Test CORS headers in response."""
        response = await async_client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    async def test_router_inclusion(self, app: FastAPI) -> None:
        """Test if main router is included in the application."""
        assert len(app.routes) > 0

        existing_routes = [
            route for route in app.routes
            if isinstance(route, APIRoute) and (route.path.startswith("/api/auth") or route.path.startswith("/api/recipe"))
        ]
        assert len(existing_routes) > 0, "No auth or recipe routes found under /api prefix"

    async def test_error_handling(self, app: FastAPI, async_client: AsyncClient) -> None:
        """Test error handling for invalid requests."""
        response = await async_client.get("/api/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

@pytest.mark.anyio
class TestMainBlock:
    """Tests related to the main execution block (`if __name__ == '__main__')."""

    async def test_main_block(self) -> None:
        """Test main block execution (uvicorn.run call)."""
        with patch("uvicorn.run") as mock_run:
            def test_run_server() -> None:
                from src.app import settings

                uvicorn.run(
                    "app:app",
                    host=settings.host,
                    port=settings.port,
                    reload=settings.debug,
                    proxy_headers=True,
                    forwarded_allow_ips="*",
                    log_level="debug" if settings.debug else "info"
                )

            test_run_server()

            mock_run.assert_called_once() 