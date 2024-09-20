from flask import session, flash, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

class UserAuth:
    def __init__(self, db):
        self.db = db

    def login(self, username, password):
        """Log user in"""
        error = None

        # Ensure username was submitted
        if not username:
            error = "must provide username"
            flash('Must provide username')
            return False, "login.html"

        # Ensure password was submitted
        elif not password:
            error = "must provide password"
            flash('Must provide password')
            return False, "login.html"

        # Query database for username
        rows = self.db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            error = "invalid username or password"
            flash('Invalid username or password')
            return False, "login.html"

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # User successfully logged in
        flash('You were successfully signed in!')
        return True, "/"

    def logout(self):
        """Log user out"""
        session.clear()

    def register(self, username, email, password, confirmation):
        """Register a new user"""
        error = None

        # Ensure all fields are provided
        if not username:
            error = "must provide username"
            flash('Must provide username')
            return False, "register.html"
        elif not password:
            error = "must provide password"
            flash('Must provide password')
            return False, "register.html"
        elif not email:
            error = "must provide an e-mail"
            flash('Must provide an e-mail')
            return False, "register.html"

        # Check if username already exists
        existing_username = self.db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_username:
            error = "username is already taken"
            flash('username is already taken')
            return False, "register.html"

        # Check if email already exists
        existing_email = self.db.execute("SELECT * FROM users WHERE email = ?", email)
        if existing_email:
            error = "email is already taken"
            flash('E-mail is already taken')
            return False, "register.html"

        # Check if passwords match
        if password != confirmation:
            error = "Password does not match"
            flash('Password does not match')
            return False, "register.html"

        # Validate password
        if not self.password_validation(password):
            error = "Invalid password."
            flash('Invalid password')
            return False, "register.html"

        # Hash the password
        hashed = generate_password_hash(password)

        # Insert the new user into the database
        self.db.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)", username, email, hashed)
        flash('You were successfully registered. Sign in to start!')
        return True, "/"

    def password_validation(self, password):
        symbols = ['!', '#', '?', '%', '$', '&']
        if len(password) < 8:
            flash("password must provide min. 8 characters")
            return False
        elif len(password) > 20:
            flash("password must provide max 20 characters")
            return False
        if not any(char.isdigit() for char in password):
            flash("password should contain at least one number")
            return False
        if not any(char.isupper() for char in password):
            flash("password should contain at least one uppercase letter")
            return False
        if not any(char.islower() for char in password):
            flash("password should contain at least one lowercase letter")
            return False
        if not any(char in symbols for char in password):
            flash('Password should contain at least one of the symbols !#?%$&')
            return False
        return True
