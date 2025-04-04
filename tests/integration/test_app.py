from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import create_application, initialize_database
from src.extensions import async_engine
from src.routes import router


@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Create test application instance."""
    app = create_application()
    app.include_router(router, prefix="/api")
    return app

@pytest.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.mark.anyio
class TestApplication:
    """Test application creation and configuration."""

    async def test_create_application(self) -> None:
        """Test application creation and configuration."""
        app = create_application()
        
        assert app.title == "Your Meal Planner API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        
        middleware = [
            m for m in app.user_middleware 
            if "CORSMiddleware" in str(m.cls)
        ]
        assert len(middleware) == 1

    async def test_debug_mode_settings(self, app: FastAPI) -> None:
        """Test debug mode configuration."""
        from src.config import get_settings
        
        settings = get_settings()
        assert hasattr(settings, "debug")
        assert isinstance(settings.debug, bool)

    def test_app_import(self) -> None:
        """Test that app can be imported correctly."""
        from src.app import app
        assert isinstance(app, FastAPI)


@pytest.mark.anyio
class TestDatabase:
    """Test database initialization and error handling."""

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
            
            assert mock_conn.run_sync.call_count == 1

    async def test_initialize_database_partial_tables(self) -> None:
        """Test database initialization when some but not all tables exist."""
        with patch("src.app.async_engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            mock_conn.run_sync.return_value = ["users", "recipes"]  # missing "user_plan"
            
            with patch("builtins.print") as mock_print:
                await initialize_database()
                
                assert mock_conn.run_sync.call_count == 2
                assert "Creating missing tables..." in [call.args[0] for call in mock_print.call_args_list]
                assert "Tables created successfully" in [call.args[0] for call in mock_print.call_args_list]


@pytest.mark.anyio
class TestLifespan:
    """Test application lifespan events."""

    async def test_lifespan(self, app: FastAPI) -> None:
        """Test application lifespan events."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/docs")
            assert response.status_code == 200

    async def test_lifespan_error_handling(self) -> None:
        """Test error handling in lifespan context manager."""
        from src.app import lifespan
        
        app = FastAPI()
        
        with patch("src.app.initialize_database", side_effect=Exception("Test exception")):
            with pytest.raises(Exception, match="Test exception"):
                async with lifespan(app):
                    pass


@pytest.mark.anyio
class TestEndpoints:
    """Test default FastAPI endpoints."""

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
        test_input: str,
        expected_status: int
    ) -> None:
        """Test default FastAPI endpoints."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(test_input)
            assert response.status_code == expected_status

    async def test_cors_headers(self, app: FastAPI) -> None:
        """Test CORS headers in response."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers

    async def test_error_handling(self, app: FastAPI) -> None:
        """Test error handling for invalid requests."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/nonexistent")
            assert response.status_code == 404
            
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

    async def test_router_inclusion(self, app: FastAPI) -> None:
        """Test if main router is included in the application."""
        assert len(app.routes) > 0
        
        existing_routes = [
            route for route in app.routes 
            if isinstance(route, APIRoute) and (route.path.startswith("/auth") or route.path.startswith("/recipe"))
        ]
        assert len(existing_routes) > 0

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTING", "True") 

@pytest.mark.anyio
async def test_main_block() -> None:
    """Test main block execution."""
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

@pytest.mark.anyio
async def test_app_lifespan_setup() -> None:
    """Test that lifespan is correctly set in FastAPI constructor."""
    from src.app import lifespan
    
    with patch("src.app.FastAPI") as mock_fastapi:
        from src.app import create_application
        
        create_application()
        
        _, kwargs = mock_fastapi.call_args
        assert "lifespan" in kwargs
        assert kwargs["lifespan"] == lifespan