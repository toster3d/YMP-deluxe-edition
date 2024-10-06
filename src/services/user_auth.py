from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token  # type: ignore
from flask import current_app
from cs50 import SQL  # type: ignore
from typing import Union, Dict, Any, Optional


class UserAuth:
    def __init__(self, db: SQL) -> None:  # type: ignore
        self.db: SQL = db

    def get_db(self) -> SQL:  # type: ignore
        if self.db is None:  # type: ignore
            self.db = current_app.config['db']
        return self.db  # type: ignore

    def login(self, username: str, password: str) -> tuple[bool, Union[str, Dict[str, str]]]:
        if not username or not password:
            current_app.logger.warning('Username and password are required.')
            return False, "Username and password are required."

        rows: list[dict[str, Any]] = self.get_db().execute( # type: ignore
            "SELECT * FROM users WHERE user_name = ?", username
        )
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):  # type: ignore
            current_app.logger.warning('Invalid username or password.')
            return False, "Invalid username or password."

        current_app.logger.info('Successfully signed in!')
        access_token: str = create_access_token(identity=username)
        return True, {"access_token": access_token}

    def logout(self) -> tuple[dict[str, str], int]:
        return {"message": "You have been logged out"}, 200

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

        if not self.password_validation(password):
            return False, "Password does not meet security requirements."

        existing_username: Any = self.get_db().execute( # type: ignore
            "SELECT * FROM users WHERE user_name = ?", username
        )
        if existing_username:
            return False, "Username is already taken."

        existing_email: Any = self.get_db().execute( # type: ignore
            "SELECT * FROM users WHERE email = ?", email
        )
        if existing_email:
            return False, "Email is already taken."

        hash: str = generate_password_hash(password)
        try:
            self.get_db().execute(  # type: ignore
                "INSERT INTO users (user_name, email, hash) VALUES(?, ?, ?)",
                username, email, hash
            )
            current_app.logger.info(f"User {username} registered successfully.")
            return True, "Registration successful."
        except Exception as e:
            current_app.logger.error(f"Error during registration: {e}")
            return False, str(e)

    def password_validation(self, password: str) -> bool:
        symbols: list[str] = ['!', '#', '?', '%', '$', '&']

        if len(password) < 8 or len(password) > 20:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        if not any(char in symbols for char in password):
            return False
        return True

    def get_user_id(self, username: str) -> Optional[int]:
        rows: list[dict[str, Any]] = self.get_db().execute(  # type: ignore
            "SELECT id FROM users WHERE user_name = ?", username
        )
        if len(rows) == 1:  # type: ignore
            return rows[0]["id"]  # type: ignore
        return None