from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings
from src.extensions import (
    Base,
    DbSession,
    get_async_db,
    get_async_db_context,
    test_database_connection,
)

settings = get_settings()


class TestDatabaseExtensions:

    def test_base_class(self) -> None:
        assert hasattr(Base, "metadata")
        assert isinstance(Base, type)
        assert issubclass(Base, DeclarativeBase)

    def test_db_session_alias(self) -> None:
        assert DbSession is AsyncSession

    @pytest.mark.asyncio
    async def test_get_async_db_context_success(self) -> None:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        
        with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
            async with get_async_db_context() as session:
                assert session is mock_session
                mock_session.commit.assert_not_called()
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.parametrize("error_class,error_message", [
        (OperationalError, "Test operational error"),
        (IntegrityError, "Test integrity error"),
        (OperationalError, "Connection timeout")
    ])
    @pytest.mark.asyncio
    async def test_get_async_db_context_with_db_errors(
        self, error_class: type[SQLAlchemyError], error_message: str
    ) -> None:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        
        db_error = error_class(error_message, None, Exception("Original error"))
        mock_session.commit.side_effect = db_error
        
        with patch("src.extensions.AsyncSessionLocal", return_value=mock_session), \
             patch("src.extensions.logger") as mock_logger:
            
            with pytest.raises(HTTPException) as excinfo:
                async with get_async_db_context() as _:
                    pass
            
            assert excinfo.value.status_code == 500
            assert "Database error" in excinfo.value.detail
            if error_message == "Connection timeout":
                assert "Connection timeout" in excinfo.value.detail
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            
            mock_logger.exception.assert_called_once_with("Database session error")

    @pytest.mark.asyncio
    async def test_get_async_db_success(self) -> None:
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

    @pytest.mark.asyncio
    async def test_get_async_db_with_error(self) -> None:
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

    @pytest.mark.asyncio
    async def test_database_connection_success(self) -> None:
        with patch("src.extensions.logger") as mock_logger:
            await test_database_connection()
            mock_logger.info.assert_called_with("Database connection successful")

    @pytest.mark.asyncio
    async def test_database_connection_failure(self) -> None:
        with patch("src.extensions.logger") as mock_logger, \
             patch("src.extensions.async_engine") as mock_engine:
            mock_engine.begin.side_effect = SQLAlchemyError("Test connection error")
            
            with pytest.raises(SQLAlchemyError):
                await test_database_connection()
            
            mock_logger.exception.assert_called_once_with("Database connection failed")

    @pytest.mark.asyncio
    async def test_get_async_db_context_with_generic_error(self) -> None:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        
        with patch("src.extensions.AsyncSessionLocal", return_value=mock_session):
            with pytest.raises(ValueError) as excinfo:
                async with get_async_db_context() as session:
                    assert session is mock_session
                    raise ValueError("User code error")
            
            assert "User code error" in str(excinfo.value)
            
            mock_session.close.assert_called_once()
