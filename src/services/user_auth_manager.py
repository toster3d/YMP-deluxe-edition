from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from config import get_settings
from extensions import DbSession
from jwt_utils import create_access_token
from models.recipes import User
from services.password_validator import PasswordValidator

settings = get_settings()

class AuthenticationError(Exception):
    """Base class for authentication errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingCredentialsError(AuthenticationError):
    """Raised when credentials are missing."""

    def __init__(self) -> None:
        super().__init__("Username and password are required.")


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid username or password.")


class TokenError(AuthenticationError):
    """Raised when token operations fail."""
    pass

class RegistrationError(Exception):
    """Base class for registration errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PasswordMismatchError(RegistrationError):
    """Raised when passwords don't match."""

    def __init__(self) -> None:
        super().__init__("Passwords do not match.")


class UserAuth:
    """Main authentication service."""

    def __init__(self, db: DbSession) -> None:
        """Initialize auth service with database session."""
        self.login_service = LoginService(db)
        self.registration_service = RegistrationService(db)
        self.password_validator = PasswordValidator()

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate user and return JWT token.

        Args:
            username: User's username
            password: User's password

        Returns:
            str: JWT access token

        Raises:
            MissingCredentialsError: If username or password is missing
            InvalidCredentialsError: If credentials are invalid
        """
        return await self.login_service.login(username, password)

    async def register(
        self, username: str, email: str, password: str, confirmation: str
    ) -> str:
        """
        Register new user.

        Args:
            username: Desired username
            email: User's email
            password: Desired password
            confirmation: Password confirmation

        Returns:
            str: Success message

        Raises:
            PasswordMismatchError: If passwords don't match
            RegistrationError: If registration fails
        """
        return await self.registration_service.register(
            username, email, password, confirmation
        )

    def validate_password(self, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            bool: True if password meets requirements
        """
        return self.password_validator.validate(password)


class LoginService:
    """Service handling user login."""

    def __init__(self, db: DbSession) -> None:
        """Initialize login service with database session."""
        self.db = db

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate user and create access token.

        Args:
            username: User's username
            password: User's password

        Returns:
            str: JWT access token

        Raises:
            MissingCredentialsError: If credentials are missing
            InvalidCredentialsError: If credentials are invalid
        """
        if not username or not password:
            raise MissingCredentialsError()

        result = await self.db.execute(select(User).filter_by(user_name=username))
        user: User | None = result.scalar_one_or_none()

        if not user:
            raise InvalidCredentialsError()

        if not check_password_hash(user.hash, password):
            raise InvalidCredentialsError()

        return create_access_token(user.id, username)


class RegistrationService:
    """Service handling user registration."""

    def __init__(self, db: DbSession) -> None:
        """Initialize registration service with database session."""
        self.db = db

    async def register(
        self, username: str, email: str, password: str, confirmation: str
    ) -> str:
        """Register new user."""
        if password != confirmation:
            raise PasswordMismatchError()

        result = await self.db.execute(select(User).filter_by(user_name=username))
        if result.scalar_one_or_none():
            raise RegistrationError("Username already exists")

        hashed_password = generate_password_hash(password)
        new_user = User(user_name=username, email=email, hash=hashed_password)

        try:
            self.db.add(new_user)
            await self.db.flush()
            await self.db.commit()
            return "Registration successful."
        except Exception as error:
            await self.db.rollback()
            raise RegistrationError(f"Registration failed: {str(error)}")


