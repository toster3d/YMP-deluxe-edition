from flask import session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

class UserAuth:
    def __init__(self, db):
        self.db = db

    def login(self, username, password):
        """Log user in"""
        if not username:
            flash('Must provide username')
            return False, "login.html"

        if not password:
            flash('Must provide password')
            return False, "login.html"

        rows = self.db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash('Invalid username or password')
            return False, "login.html"

        session["user_id"] = rows[0]["id"]
        flash('You were successfully signed in!')
        return True, "/"

    def logout(self):
        """Log user out"""
        session.clear()

    def register(self, username, email, password, confirmation):
        """Register a new user"""
        if not username:
            flash('Must provide username')
            return False, "register.html"

        if not password:
            flash('Must provide password')
            return False, "register.html"

        if not email:
            flash('Must provide an e-mail')
            return False, "register.html"

        existing_username = self.db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_username:
            flash('Username is already taken')
            return False, "register.html"

        existing_email = self.db.execute("SELECT * FROM users WHERE email = ?", email)
        if existing_email:
            flash('E-mail is already taken')
            return False, "register.html"

        if password != confirmation:
            flash('Password does not match')
            return False, "register.html"

        if not self.password_validation(password):
            return False, "register.html"

        hashed = generate_password_hash(password)
        self.db.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)", username, email, hashed)
        flash('You were successfully registered. Sign in to start!')
        return True, "/"

    def password_validation(self, password):
        symbols = ['!', '#', '?', '%', '$', '&']

        if len(password) < 8:
            flash("Password must provide min. 8 characters")
            return False
        if len(password) > 20:
            flash("Password must provide max 20 characters")
            return False
        if not any(char.isdigit() for char in password):
            flash("Password should contain at least one number")
            return False
        if not any(char.isupper() for char in password):
            flash("Password should contain at least one uppercase letter")
            return False
        if not any(char.islower() for char in password):
            flash("Password should contain at least one lowercase letter")
            return False
        if not any(char in symbols for char in password):
            flash('Password should contain at least one of the symbols !#?%$&')
            return False
        return True
