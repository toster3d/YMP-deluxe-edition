import logging
from flask import Flask
from cs50 import SQL
import os

db = None  # Initialize db variable

def create_app():
    global db
    app = Flask(__name__, 
                template_folder=os.path.abspath('src/templates'),
                static_folder=os.path.abspath('src/static'))
    app.config['SECRET_KEY'] = 'your-secret-key'  # Flask secret key

    # Database path
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "recipes.db")
    
    # Create database if it doesn't exist
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'w').close()  # Creates an empty file
    
    db = SQL(f"sqlite:///{DB_PATH}")
    init_db(db)

    # Pass db instance to service classes
    from .services.user_auth import UserAuth
    from .services.recipe_manager import RecipeManager
    from .services.user_plan_manager import UserPlanManager
    from .services.shopping_list_service import ShoppingListService

    user_auth = UserAuth(db)
    recipe_manager = RecipeManager(db)
    user_plan_manager = UserPlanManager(db)
    shopping_list_service = ShoppingListService(user_plan_manager, recipe_manager)

    # Add services to app configuration
    app.config['services'] = {
        'user_auth': user_auth,
        'recipe_manager': recipe_manager,
        'user_plan_manager': user_plan_manager,
        'shopping_list_service': shopping_list_service
    }

    return app

def configure_app(app):
    app.config['DEBUG'] = True  # Can be set to False in production
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_TYPE'] = 'filesystem'

    
    # Logger configuration
    logging.basicConfig(level=logging.INFO)
    app.logger = logging.getLogger(__name__)

    return app

def init_db(db):
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    )
    """)
    # Add other tables here if needed