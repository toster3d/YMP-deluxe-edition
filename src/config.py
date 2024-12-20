import os
import logging
from dotenv import load_dotenv
from flask import Flask
from extensions import db
from datetime import timedelta

dotenv_path: str = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key')
    DEBUG = os.environ.get('DEBUG', None) is not None
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback_jwt_secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or f'sqlite:////{os.path.join("/app", "src", "instance", "recipes.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PREFIX = 'token_blacklist:'
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

def create_app(config_class: type[Config] = Config) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_class)
    
    log_level: int = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    logging.getLogger('flask_app').setLevel(log_level)
    app.logger.setLevel(log_level)
    
    db.init_app(app)
    return app
