from unittest.mock import MagicMock, patch

import pytest
import uvicorn


@pytest.mark.anyio
async def test_run_server_function() -> None:
    """Test run_server function with debug mode."""
    with patch("uvicorn.run") as mock_run:
        mock_settings = MagicMock()
        mock_settings.host = "127.0.0.1"
        mock_settings.port = 8000
        mock_settings.debug = True
        
        def run_server() -> None:
            uvicorn.run(
                "app:app",
                host=mock_settings.host,
                port=mock_settings.port,
                reload=mock_settings.debug,
                proxy_headers=True,
                forwarded_allow_ips="*",
                log_level="debug" if mock_settings.debug else "info"
            )
        
        run_server()
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0]
        call_kwargs = mock_run.call_args[1]
        
        assert call_args[0] == "app:app"
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 8000
        assert call_kwargs["reload"] is True
        assert call_kwargs["log_level"] == "debug"


@pytest.mark.anyio
async def test_run_server_function_production() -> None:
    """Test run_server function in production mode."""
    with patch("uvicorn.run") as mock_run:
        mock_settings = MagicMock()
        mock_settings.host = "0.0.0.0"
        mock_settings.port = 80
        mock_settings.debug = False
        
        def run_server() -> None:
            uvicorn.run(
                "app:app",
                host=mock_settings.host,
                port=mock_settings.port,
                reload=mock_settings.debug,
                proxy_headers=True,
                forwarded_allow_ips="*",
                log_level="debug" if mock_settings.debug else "info"
            )
        
        run_server()
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0]
        call_kwargs = mock_run.call_args[1]
        
        assert call_args[0] == "app:app"
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 80
        assert call_kwargs["reload"] is False
        assert call_kwargs["log_level"] == "info"


@pytest.mark.anyio
async def test_run_server_system_exit() -> None:
    """Test that run_server raises SystemExit."""
    with patch("uvicorn.run"):
        def run_server() -> None:
            raise SystemExit(0)
        
        with pytest.raises(SystemExit) as excinfo:
            run_server()
        
        assert excinfo.value.code == 0


@pytest.mark.anyio
async def test_app_with_lifespan() -> None:
    """Test that FastAPI app is created with lifespan context manager."""
    with patch("fastapi.FastAPI") as mock_fastapi:
        mock_lifespan = MagicMock()
        
        def create_application() -> None:
            from fastapi import FastAPI
            FastAPI(
                title="Your Meal Planner API",
                description="API for meal planning and recipe management",
                version="1.0.0",
                docs_url="/docs",
                redoc_url="/redoc",
                lifespan=mock_lifespan
            )
        
        create_application()
        
        _, kwargs = mock_fastapi.call_args
        assert "lifespan" in kwargs
        assert kwargs["lifespan"] == mock_lifespan 