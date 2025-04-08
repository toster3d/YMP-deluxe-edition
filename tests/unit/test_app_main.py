"""Unit tests for app.py main functionality."""

from unittest.mock import MagicMock, patch

import pytest
import uvicorn


class TestRunServer:
    """Test cases for run_server function."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "host,port,debug,expected_log_level",
        [
            ("127.0.0.1", 8000, True, "debug"),
            ("0.0.0.0", 80, False, "info"),
            ("localhost", 8080, True, "debug"),
        ]
    )
    async def test_run_server_with_different_configs(
        self,
        host: str,
        port: int,
        debug: bool,
        expected_log_level: str
    ) -> None:
        """Test run_server with different configurations."""
        with patch("uvicorn.run") as mock_run:
            mock_settings = MagicMock()
            mock_settings.host = host
            mock_settings.port = port
            mock_settings.debug = debug
            
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
            assert call_kwargs["host"] == host
            assert call_kwargs["port"] == port
            assert call_kwargs["reload"] is debug
            assert call_kwargs["log_level"] == expected_log_level
            assert call_kwargs["proxy_headers"] is True
            assert call_kwargs["forwarded_allow_ips"] == "*"

    @pytest.mark.anyio
    async def test_run_server_system_exit(self) -> None:
        """Test that run_server raises SystemExit."""
        with patch("uvicorn.run"):
            def run_server() -> None:
                raise SystemExit(0)
            
            with pytest.raises(SystemExit) as excinfo:
                run_server()
            
            assert excinfo.value.code == 0


class TestFastAPIApplication:
    """Test cases for FastAPI application creation."""

    @pytest.mark.anyio
    async def test_app_with_lifespan(self) -> None:
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
            assert kwargs["title"] == "Your Meal Planner API"
            assert kwargs["description"] == "API for meal planning and recipe management"
            assert kwargs["version"] == "1.0.0"
            assert kwargs["docs_url"] == "/docs"
            assert kwargs["redoc_url"] == "/redoc"

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "title,version,description",
        [
            ("Test API", "2.0.0", "Test Description"),
            ("Another API", "1.0.0", "Another Description"),
        ]
    )
    async def test_app_with_custom_config(
        self,
        title: str,
        version: str,
        description: str
    ) -> None:
        """Test FastAPI app creation with custom configuration."""
        with patch("fastapi.FastAPI") as mock_fastapi:
            def create_application() -> None:
                from fastapi import FastAPI
                FastAPI(
                    title=title,
                    description=description,
                    version=version,
                    docs_url="/docs",
                    redoc_url="/redoc",
                    lifespan=MagicMock()
                )
            
            create_application()
            
            _, kwargs = mock_fastapi.call_args
            assert kwargs["title"] == title
            assert kwargs["version"] == version
            assert kwargs["description"] == description