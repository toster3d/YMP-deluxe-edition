import logging
from flask import Flask
from cs50 import SQL # type: ignore
import os
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

load_dotenv()

# Logger configuration
logger: logging.Logger = logging.getLogger('app_logger')
logger.setLevel(logging.INFO)

# Tworzenie pojedynczego obsługiwacza konsoli
console_handler: logging.StreamHandler = logging.StreamHandler() # type: ignore

# Create a simple formatter and add it to the handler
formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler) # type: ignore

def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    CURRENT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH: str = os.path.join(CURRENT_DIR, "recipes.db")
    db: SQL = SQL(f"sqlite:///{DB_PATH}") # type: ignore

    app.config['db'] = db

    # Assign the configured logger to the Flask app
    app.logger = logger  # type: ignore
    # Inicjalizacja JWT
    JWTManager(app)

    return app

def configure_app(app: Flask) -> Flask:
    app.config['DEBUG'] = os.getenv('DEBUG') == 'True'  # Can be set to False in production
    app.config['TEMPLATES_AUTO_RELOAD'] = os.getenv('TEMPLATES_AUTO_RELOAD') == 'True'
    app.config['SESSION_PERMANENT'] = os.getenv('SESSION_PERMANENT') == 'True'
    app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE')

    return app
