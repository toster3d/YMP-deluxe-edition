from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_token_storage  # type: ignore
from extensions import get_async_db
from jwt_utils import verify_jwt
from services.user_auth_manager import (
    InvalidCredentialsError,
    MissingCredentialsError,
    RegistrationError,
    TokenError,
    UserAuth,
)
from token_storage import RedisTokenStorage

from .pydantic_schemas import RegisterSchema, TokenResponse


class AuthResource:
    """Resource handling user authentication."""

    def __init__(self, db: AsyncSession = Depends(get_async_db)):
        """Initialize auth resource with database session."""
        self.user_auth = UserAuth(db)

    async def login_with_form(
        self, form_data: OAuth2PasswordRequestForm
    ) -> TokenResponse:
        """
        OAuth2 compatible token login.

        Args:
            form_data: OAuth2 form containing username and password

        Returns:
            TokenResponse: Access token response

        Raises:
            HTTPException: If authentication fails
        """
        try:
            access_token = await self.user_auth.login(
                username=form_data.username, password=form_data.password
            )
            return TokenResponse(access_token=access_token, token_type="bearer")
        except MissingCredentialsError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except InvalidCredentialsError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except TokenError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during login",
            ) from e


class RegisterResource:
    """Resource handling user registration."""

    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize register resource with database session."""
        self.db = db
        self.user_auth = UserAuth(db)

    async def post(self, register_data: RegisterSchema) -> dict[str, str]:
        """Register new user."""
        try:
            message = await self.user_auth.register(
                register_data.username,
                register_data.email,
                register_data.password,
                register_data.confirmation,
            )
            return {"message": message}
        except RegistrationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during registration: {str(e)}",
            )


class LogoutResource:
    """Resource handling user logout."""

    def __init__(
        self,
        token_storage: Annotated[RedisTokenStorage, Depends(get_token_storage)],  # type: ignore
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Initialize logout resource with database session and token storage."""
        self.db = db
        self.token_storage = token_storage

    async def post(self, token: str) -> dict[str, str]:
        """
        Logout user and invalidate token.

        Args:
            token: JWT token to invalidate

        Returns:
            dict: Logout confirmation message
        """
        try:
            payload = verify_jwt(token)
            jti = payload.get("jti")
            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token data: missing jti",
                )
            expires_delta = timedelta(minutes=30)
            await self.token_storage.store(jti, expires_delta=expires_delta)
            return {"message": "Logout successful!"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during logout: {str(e)}",
            )
