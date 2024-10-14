from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from flask import current_app
from typing import Literal, Union, Optional, Any
from src.models.recipes import User


class UserAuth:
    def __init__(self, db: Any) -> None:
        self.db: Any = db

    def login(self, username: str, password: str) -> tuple[bool, Union[str, dict[str, str]]]:
        current_app.logger.info(f"Attempting to log in user: {username}")
        if not username or not password:
            current_app.logger.warning('Username and password are required.')
            return False, "Username and password are required."

        user: Optional[User] = User.query.filter_by(user_name=username).first()
        current_app.logger.info(f"User found: {user}")

        if user is None:
            current_app.logger.warning('Invalid username or password.')
            return False, "Invalid username or password."

        if not check_password_hash(user.hash, password):
            current_app.logger.warning('Invalid username or password.')
            return False, "Invalid username or password."

        user_id: int = user.id
        current_app.logger.info(f"User ID for {username}: {user_id}")

        access_token: str = create_access_token(identity=user_id)
        return True, {"access_token": access_token}

    def register(
        self,
        username: str,
        email: str,
        password: str,
        confirmation: str
    ) -> tuple[bool, str]:
        if not username or not email or not password or not confirmation:
            return False, "All fields are required."

        if password != confirmation:
            return False, "Passwords do not match."

        hashed_password = generate_password_hash(password)
        new_user = User(user_name=username, email=email, hash=hashed_password)

        try:
            self.db.session.add(new_user)
            self.db.session.commit()
            current_app.logger.info(f"User {username} registered successfully.")
            return True, "Registration successful."
        except Exception as e:
            self.db.session.rollback()
            current_app.logger.error(f"Error during registration: {e}")
            return False, str(e)

    def password_validation(self, password: str) -> bool:
        symbols: set[str] = {'!', '#', '?', '%', '$', '&'}
        if not (8 <= len(password) <= 20):
            return False

        has_digit = has_upper = has_lower = has_symbol = False

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

    def get_user_id(self, username: str) -> Optional[int]:
        user: Optional[User] = User.query.filter_by(user_name=username).first()
        if user is None:
            return None
        return user.id 
