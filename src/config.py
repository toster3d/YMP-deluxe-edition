import os
import logging
from dotenv import load_dotenv
from flask import Flask
from src.extensions import db

dotenv_path: str = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_secret_key'
    DEBUG = os.environ.get('DEBUG') in ('true', '1', 't')
    TEMPLATES_AUTO_RELOAD = os.environ.get('TEMPLATES_AUTO_RELOAD') in ('true', '1', 't')
    SESSION_PERMANENT = os.environ.get('SESSION_PERMANENT') in ('true', '1', 't')
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'filesystem'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'fallback_jwt_secret'
    JWT_BLACKLIST: set[str] = set()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///recipes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app(config_class: type[Config] = Config) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_class)

    log_level: int = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    logging.getLogger('flask_app').setLevel(log_level)
    app.logger.setLevel(log_level)

    db.init_app(app)
    
    return app
