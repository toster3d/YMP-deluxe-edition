import os
import logging
from dotenv import load_dotenv
from flask import Flask
from cs50 import SQL  # type: ignore


dotenv_path: str = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key')
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    TEMPLATES_AUTO_RELOAD = os.environ.get(
        'TEMPLATES_AUTO_RELOAD', 'False'
    ).lower() in ('true', '1', 't')
    SESSION_PERMANENT = os.environ.get(
        'SESSION_PERMANENT', 'False'
    ).lower() in ('true', '1', 't')
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback_jwt_secret')
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///recipes.db')
    JWT_BLACKLIST: set[str] = set()


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    logging.getLogger('flask_app').setLevel(log_level)
    app.logger.setLevel(log_level)

    db: SQL = SQL(app.config['DATABASE_URI'])  # type: ignore
    app.config['db'] = db

    return app
