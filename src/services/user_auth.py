from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token  # type: ignore
from flask import current_app
from cs50 import SQL  # type: ignore
from typing import Union, Any


class UserAuth:
    def __init__(self, db: SQL) -> None:  # type: ignore
        self.db: SQL = db

    def get_db(self) -> SQL:  # type: ignore
        if self.db is None:  # type: ignore
            self.db = current_app.config['db']
        return self.db  # type: ignore

    def login(self, username: str, password: str) -> tuple[bool, Union[str, dict[str, str]]]:
        if not username or not password:
            current_app.logger.warning('Username and password are required.')
            return False, "Username and password are required."

        rows: list[dict[str, Any]] = self.get_db().execute(  # type: ignore
            "SELECT * FROM users WHERE user_name = ?", username
        )

        if len(rows) != 1:  # type: ignore
            current_app.logger.warning('Invalid username or password.')
            return False, "Invalid username or password."

        if not check_password_hash(rows[0]["hash"], password):  # type: ignore
            current_app.logger.warning('Invalid username or password.')
            return False, "Invalid username or password."

        user_id: Any = rows[0]["id"]
        current_app.logger.info(f"User ID for {username}: {user_id}")

        access_token: str = create_access_token(identity=user_id)
        return True, {"access_token": access_token}

    def logout(self):
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

        existing_username: Any = self.get_db().execute(  # type: ignore
            "SELECT * FROM users WHERE user_name = ?", username
        )
        if existing_username:
            return False, "Username is already taken."

        existing_email: Any = self.get_db().execute(  # type: ignore
            "SELECT * FROM users WHERE email = ?", email
        )
        if existing_email:
            return False, "Email is already taken."

        hash: str = generate_password_hash(password)
        try:
            self.get_db().execute(  # type: ignore
                "INSERT INTO users (user_name, email, hash) VALUES (?, ?, ?)",
                username, email, hash
            )
            current_app.logger.info(f"User {username} registered successfully.")
            return True, "Registration successful."
        except Exception as e:
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

    def get_user_id(self, username: str) -> int | None:
        rows: list[dict[str, Any]] = self.get_db().execute(  # type: ignore
            "SELECT id FROM users WHERE user_name = ?", username
        )
        if len(rows) == 1:  # type: ignore
            return rows[0]["id"]  # type: ignore
        return None