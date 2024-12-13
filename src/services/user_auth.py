from typing import Any, Coroutine

from fastapi import HTTPException
from flask import current_app
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from werkzeug.security import check_password_hash, generate_password_hash

from models.recipes import User


class UserAuth:
    def __init__(self, db: AsyncSession) -> None:
        self.login_service = LoginService(db)
        self.registration_service = RegistrationService(db)
        self.password_validator = PasswordValidator()

    def login(self, username: str, password: str) -> Coroutine[Any, Any, str]:
        return self.login_service.login(username, password)

    async def register(self, username: str, email: str, password: str, confirmation: str) -> str:
        return await self.registration_service.register(username, email, password, confirmation)

    def validate_password(self, password: str) -> bool:
        return self.password_validator.validate(password)

class LoginService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def login(self, username: str, password: str) -> str:
        # Asynchroniczne zapytanie do bazy
        result = await self.db.execute(
            select(User).filter_by(user_name=username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not check_password_hash(user.hash, password):
            raise HTTPException(status_code=401, detail="Invalid credentials")


        access_token: str = create_access_token(
            identity=str(user.id),
            additional_claims={
                "username": username,
                "type": "access"
            }
        )
        return access_token

class RegistrationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, username: str, email: str, password: str, confirmation: str) -> str:
        if password != confirmation:
            raise PasswordMismatchError()

        hashed_password: str = generate_password_hash(password)
        new_user: User = User(user_name=username, email=email, hash=hashed_password)
        try:
            self.db.add(new_user)
            await self.db.commit()
            return "Registration successful."
        except Exception as error:
            await self.db.rollback()
            raise RegistrationError("Registration failed due to an unexpected error.")

class PasswordValidator:
    def validate(self, password: str) -> bool:
        symbols: set[str] = {'!', '#', '?', '%', '$', '&'}
        if not (8 <= len(password) <= 20):
            return False

        has_digit: bool = False
        has_upper: bool = False
        has_lower: bool = False
        has_symbol: bool = False

        for char in password:
            if char.isdigit():
                has_digit = True
            elif char.isupper():
                has_upper = True
            elif char.islower():
                has_lower = True
            elif char in symbols:
                has_symbol = True

            if has_digit and has_upper and has_lower and has_symbol:
                return True

        return has_digit and has_upper and has_lower and has_symbol

class AuthenticationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Username and password are required.")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Invalid username or password.")


class RegistrationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class PasswordMismatchError(RegistrationError):
    def __init__(self) -> None:
        super().__init__("Passwords do not match.")



    # async def register(self, username: str, email: str, password: str) -> User:
    #     # Sprawdzenie, czy użytkownik już istnieje
    #     existing_user = await self.db.execute(
    #         select(User).filter_by(user_name=username)
    #     )
    #     if existing_user.scalar_one_or_none():
    #         raise HTTPException(status_code=400, detail="Username already exists")

    #     # Hashowanie hasła
    #     hashed_password = generate_password_hash(password)
        
    #     # Tworzenie nowego użytkownika
    #     new_user = User(
    #         user_name=username, 
    #         email=email, 
    #         hash=hashed_password
    #     )
        
    #     # Dodanie i zatwierdzenie
    #     self.db.add(new_user)
    #     await self.db.commit()
    #     await self.db.refresh(new_user)
        
    #     return new_user

