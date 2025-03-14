from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.extensions import (
    get_async_db,
    get_async_db_context,
    test_database_connection,
)


@pytest.mark.anyio
async def test_get_async_db_context_success() -> None:
    """Test successful database session with context manager."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        async with get_async_db_context() as session:
            assert session is mock_session
            mock_session.commit.assert_not_called()
        
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_get_async_db_context_with_db_error() -> None:
    """Test database session with SQLAlchemy error."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    db_error = SQLAlchemyError("Test database error")
    mock_session.commit.side_effect = db_error
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session), \
         patch("src.extensions.logger") as mock_logger:
        
        with pytest.raises(HTTPException) as excinfo:
            async with get_async_db_context() as _:
                pass
        
        assert excinfo.value.status_code == 500
        assert "Database error" in excinfo.value.detail
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        
        mock_logger.exception.assert_called_once_with("Database session error")


@pytest.mark.anyio
async def test_get_async_db_success() -> None:
    """Test successful async database session dependency."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        db_gen = get_async_db()
        session = await anext(db_gen)
        
        assert session is mock_session
        
        try:
            await db_gen.aclose()
        except StopAsyncIteration:
            pass
        
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_get_async_db_with_error() -> None:
    """Test async database session dependency with error."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        db_gen = get_async_db()
        session = await anext(db_gen)
        
        assert session is mock_session
        
        try:
            await db_gen.athrow(ValueError("View function error"))
        except ValueError as e:
            assert "View function error" in str(e)
        except StopAsyncIteration:
            pass
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_database_connection_functionality() -> None:
    """Test database connection functionality as a whole."""
    with patch("src.extensions.logger") as mock_logger:
        await test_database_connection()
        mock_logger.info.assert_called_with("Database connection successful")
        
        mock_logger.reset_mock()
        
        with patch("src.extensions.async_engine") as mock_engine:
            mock_engine.begin.side_effect = SQLAlchemyError("Test connection error")
            
            with pytest.raises(SQLAlchemyError):
                await test_database_connection()
            
            mock_logger.exception.assert_called_with("Database connection failed")


@pytest.mark.anyio
async def test_get_async_db_context_with_generic_error() -> None:
    """Test database session with generic error in user code."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        with pytest.raises(ValueError) as excinfo:
            async with get_async_db_context() as session:
                assert session is mock_session
                raise ValueError("User code error")
        
        assert "User code error" in str(excinfo.value)
        
        mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_get_async_db() -> None:
    """Test async database session dependency."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        db_gen = get_async_db()
        session = await anext(db_gen)
        
        assert session is mock_session
        
        try:
            await db_gen.aclose()
        except StopAsyncIteration:
            pass
        
        mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_get_async_db_with_generic_error() -> None:
    """Test async database session dependency with generic error."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    
    with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
        db_gen = get_async_db()
        session = await anext(db_gen)
        
        assert session is mock_session
        
        try:
            await db_gen.athrow(ValueError("View function error"))
        except ValueError as e:
            assert "View function error" in str(e)
        except StopAsyncIteration:
            pass
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
