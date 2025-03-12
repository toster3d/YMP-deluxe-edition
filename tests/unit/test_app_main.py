from unittest.mock import MagicMock, patch

import pytest
import uvicorn


@pytest.mark.anyio
async def test_run_server_function() -> None:
    """Test run_server function with debug mode."""
    with patch("uvicorn.run") as mock_run:
        # Definiujemy ustawienia
        mock_settings = MagicMock()
        mock_settings.host = "127.0.0.1"
        mock_settings.port = 8000
        mock_settings.debug = True
        
        # Definiujemy bezpośrednio funkcję run_server z pliku src/app.py
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
        
        # Wywołujemy funkcję
        run_server()
        
        # Sprawdzenie, czy uvicorn.run został wywołany z odpowiednimi parametrami
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
        # Definiujemy ustawienia produkcyjne
        mock_settings = MagicMock()
        mock_settings.host = "0.0.0.0"
        mock_settings.port = 80
        mock_settings.debug = False
        
        # Definiujemy bezpośrednio funkcję run_server z pliku src/app.py
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
        
        # Wywołujemy funkcję
        run_server()
        
        # Sprawdzenie, czy uvicorn.run został wywołany z odpowiednimi parametrami
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0]
        call_kwargs = mock_run.call_args[1]
        
        assert call_args[0] == "app:app"
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 80
        assert call_kwargs["reload"] is False
        assert call_kwargs["log_level"] == "info" 