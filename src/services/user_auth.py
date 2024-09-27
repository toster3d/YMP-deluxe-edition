import logging
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserAuth:
    """
    A class to handle user authentication operations.

    This class provides methods for user login, logout, registration,
    and password validation.
    """

    def __init__(self, db):
        """
        Initialize the UserAuth instance.

        Args:
            db: The database connection object.
        """
        self.db = db

    def login(self, username, password):
        """
        Authenticate a user and log them in.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            tuple: A boolean indicating success and a string with the redirect path.
        """
        if not username:
            logger.warning('Must provide username')
            return False, "login.html"

        if not password:
            logger.warning('Must provide password')
            return False, "login.html"

        rows = self.db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            logger.warning('Invalid username or password')
            return False, "login.html"

        session["user_id"] = rows[0]["id"]
        logger.info('You were successfully signed in!')
        return True, "/"

    def logout(self):
        """Log the current user out by clearing the session."""
        session.clear()

    def register(self, username, email, password, confirmation):
        """
        Register a new user.

        Args:
            username (str): The desired username.
            email (str): The user's email address.
            password (str): The desired password.
            confirmation (str): Password confirmation.

        Returns:
            tuple: A boolean indicating success and a string with the redirect path.
        """
        if not username:
            logger.warning('Must provide username')
            return False, "register.html"

        if not password:
            logger.warning('Must provide password')
            return False, "register.html"

        if not email:
            logger.warning('Must provide an e-mail')
            return False, "register.html"

        existing_username = self.db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )
        if existing_username:
            logger.warning('Username is already taken')
            return False, "register.html"

        existing_email = self.db.execute(
            "SELECT * FROM users WHERE email = ?", email
        )
        if existing_email:
            logger.warning('E-mail is already taken')
            return False, "register.html"

        if password != confirmation:
            logger.warning('Password does not match')
            return False, "register.html"

        if not self.password_validation(password):
            return False, "register.html"

        hashed = generate_password_hash(password)
        self.db.execute(
            "INSERT INTO users (username, email, hash) VALUES(?, ?, ?)",
            username, email, hashed
        )
        logger.info('You were successfully registered. Sign in to start!')
        return True, "/"

    def password_validation(self, password):
        """
        Validate the password against security criteria.

        Args:
            password (str): The password to validate.

        Returns:
            bool: True if the password meets all criteria, False otherwise.
        """
        symbols = ['!', '#', '?', '%', '$', '&']

        if len(password) < 8:
            logger.warning("Password must provide min. 8 characters")
            return False
        if len(password) > 20:
            logger.warning("Password must provide max 20 characters")
            return False
        if not any(char.isdigit() for char in password):
            logger.warning("Password should contain at least one number")
            return False
        if not any(char.isupper() for char in password):
            logger.warning("Password should contain at least one uppercase letter")
            return False
        if not any(char.islower() for char in password):
            logger.warning("Password should contain at least one lowercase letter")
            return False
        if not any(char in symbols for char in password):
            logger.warning('Password should contain at least one of the symbols !#?%$&')
            return False
        return True
