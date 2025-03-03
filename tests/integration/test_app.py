from typing import AsyncGenerator

import pytest
import pytest_asyncio
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

@pytest_asyncio.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.mark.anyio
async def test_create_application() -> None:
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

@pytest.mark.anyio
async def test_initialize_database() -> None:
    """Test database initialization."""
    await initialize_database()
    
    required_tables = {"users", "recipes", "user_plan"}
    
    async with async_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        existing_tables = {row[0] for row in result.fetchall()}
        
        assert required_tables.issubset(existing_tables)

@pytest.mark.anyio
async def test_lifespan(app: FastAPI) -> None:
    """Test application lifespan events."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        response = await client.get("/")
        assert response.status_code in (404, 200)

@pytest.mark.anyio
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
    app: FastAPI,
    test_input: str,
    expected_status: int
) -> None:
    """Test default FastAPI endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(test_input)
        assert response.status_code == expected_status

@pytest.mark.anyio
async def test_cors_headers(app: FastAPI) -> None:
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

@pytest.mark.anyio
async def test_router_inclusion(app: FastAPI) -> None:
    """Test if main router is included in the application."""
    assert len(app.routes) > 0
    
    existing_routes = [
        route for route in app.routes 
        if isinstance(route, APIRoute) and (route.path.startswith("/auth") or route.path.startswith("/recipe"))
    ]
    assert len(existing_routes) > 0

@pytest.mark.anyio
async def test_error_handling(app: FastAPI) -> None:
    """Test error handling for invalid requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

@pytest.mark.anyio
async def test_debug_mode_settings(app: FastAPI) -> None:
    """Test debug mode configuration."""
    from src.config import get_settings
    
    settings = get_settings()
    assert hasattr(settings, "debug")
    assert isinstance(settings.debug, bool)

def test_app_import() -> None:
    """Test that app can be imported correctly."""
    from src.app import app
    assert isinstance(app, FastAPI)

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTING", "True") 
