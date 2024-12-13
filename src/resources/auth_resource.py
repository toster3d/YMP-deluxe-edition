from datetime import timedelta
from typing import cast

from fastapi import Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from extensions import get_async_db
from services.user_auth import (
    InvalidCredentialsError,
    MissingCredentialsError,
    RegistrationError,
    UserAuth,
)
from token_storage import RedisTokenStorage
from pydantic_schemas import LoginSchema, RegisterSchema


class AuthResource:
    def __init__(self, db: AsyncSession = Depends(get_async_db)):
        self.user_auth = UserAuth(db)

    async def post(self, login_data: LoginSchema) -> dict[str, str]:
        try:
            access_token: str = await self.user_auth.login(login_data.username, login_data.password)
            return {
                "message": "Login successful!",
                "access_token": access_token
            }
        except MissingCredentialsError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except InvalidCredentialsError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception:
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


class RegisterResource:
    def __init__(self, db: AsyncSession = Depends(get_async_db)):
        self.user_auth = UserAuth(db)

    async def post(self, register_data: RegisterSchema) -> dict[str, str]:
        try:
            await self.user_auth.register(
                register_data.username, 
                register_data.email, 
                register_data.password, 
                register_data.confirmation
            )
            return {"message": "Registration successful!"}
        except ValidationError as err:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        except RegistrationError as e:
            raise HTTPException(status_code=500, detail="Registration failed.")
        except Exception:
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


class LogoutResource:
    def __init__(self, db: AsyncSession = Depends(get_async_db), token_storage: RedisTokenStorage = Depends()):
        self.db = db
        self.token_storage = token_storage

    async def post(self, jwt_data: dict) -> dict[str, str]:
        try:
            jti: str = jwt_data['jti']
            expires_delta = timedelta(minutes=30)  # Configure this based on your needs
            self.token_storage.store(jti, expires_delta=expires_delta)
            return {"message": "Logout successful!"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred during logout: {str(e)}"
            )
