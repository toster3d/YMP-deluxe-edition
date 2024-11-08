from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token #type: ignore
from flask import current_app
from models.recipes import User
from flask_sqlalchemy import SQLAlchemy


class UserAuth:
    def __init__(self, db: SQLAlchemy) -> None:
        self.login_service = LoginService(db)
        self.registration_service = RegistrationService(db)
        self.password_validator = PasswordValidator()

    def login(self, username: str, password: str) -> str:
        return self.login_service.login(username, password)

    def register(self, username: str, email: str, password: str, confirmation: str) -> str:
        return self.registration_service.register(username, email, password, confirmation)

    def validate_password(self, password: str) -> bool:
        return self.password_validator.validate(password)


class LoginService:
    def __init__(self, db: SQLAlchemy) -> None:
        self.db: SQLAlchemy = db

    def login(self, username: str, password: str) -> str:
        if not username or not password:
            raise MissingCredentialsError()

        user: User | None = self.db.session.query(User).filter_by(user_name=username).first()
        current_app.logger.info(f"User found: {user}")

        if user is None:
            raise InvalidCredentialsError()

        if not check_password_hash(user.hash, password):
            current_app.logger.warning('Invalid username or password.')
            raise InvalidCredentialsError()

        user_id = user.id
        current_app.logger.info(f"User ID for {username}: {user_id}")

        access_token: str = create_access_token(identity=user_id)
        return access_token

class RegistrationService:
    def __init__(self, db: SQLAlchemy) -> None:
        self.db: SQLAlchemy = db

    def register(self, username: str, email: str, password: str, confirmation: str) -> str:
        if password != confirmation:
            raise PasswordMismatchError()

        hashed_password: str = generate_password_hash(password)
        new_user: User = User(user_name=username, email=email, hash=hashed_password)
        try:
            self.db.session.add(new_user)
            self.db.session.commit()
            current_app.logger.info(f"User {username} registered successfully.")
            return "Registration successful."
        except Exception as error:
            self.db.session.rollback()
            current_app.logger.error(f"Error during registration: {error}")
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
