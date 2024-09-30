import logging
from flask import Flask
from cs50 import SQL
import os

db = None  # Inicjalizacja zmiennej db

def create_app():
    global db
    app = Flask(__name__, 
                template_folder=os.path.abspath('src/templates'),
                static_folder=os.path.abspath('src/static'))
    app.config['SECRET_KEY'] = 'your-secret-key'  # Klucz dla Flask

    # Ścieżka do bazy danych
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "recipes.db")
    
    # Tworzenie bazy danych, jeśli nie istnieje
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'w').close()  # Tworzy pusty plik
    
    db = SQL(f"sqlite:///{DB_PATH}")
    init_db(db)  # Dodaj tę linię

    # Przekazanie instancji db do klas usługowych
    from .services.user_auth import UserAuth
    from .services.recipe_manager import RecipeManager
    from .services.user_plan_manager import UserPlanManager
    from .services.shopping_list_service import ShoppingListService

    user_auth = UserAuth(db)
    recipe_manager = RecipeManager(db)
    user_plan_manager = UserPlanManager(db)
    shopping_list_service = ShoppingListService(user_plan_manager, recipe_manager)

    # Dodajemy serwisy do konfiguracji aplikacji
    app.config['services'] = {
        'user_auth': user_auth,
        'recipe_manager': recipe_manager,
        'user_plan_manager': user_plan_manager,
        'shopping_list_service': shopping_list_service
    }

    return app

def configure_app(app):
    app.config['DEBUG'] = True  # Można ustawić False w produkcji
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_TYPE'] = 'filesystem'

    
    # Konfiguracja loggera
    logging.basicConfig(level=logging.INFO)
    app.logger = logging.getLogger(__name__)


    return app


    # Ścieżka do bazy danych
    #CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    #DB_PATH = os.path.join(CURRENT_DIR, "recipes.db")  # Umieść bazę danych w głównym folderze projektu
    #app.config['DATABASE_PATH'] = DB_PATH

def init_db(db):
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    )
    """)
    # Dodaj tutaj inne tabele, jeśli są potrzebne