#from flask import Flask
#from cs50 import SQL
#import os

# Inicjalizacja bazy danych CS50
#def create_app():
 #   app = Flask(__name__)
    #app.config['SECRET_KEY'] = 'your-secret-key'  # Klucz dla Flask

    # Ścieżka do bazy danych
    #CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #DB_PATH = os.path.join(CURRENT_DIR, "recipes.db")
    #db = SQL(f"sqlite:///{DB_PATH}")

    # Przekazanie instancji db do klas usługowych
    #from services.user_auth import UserAuth
    #from services.recipe_manager import RecipeManager
    #from services.user_plan_manager import UserPlanManager
    #from services.shopping_list_service import ShoppingListService

    #user_auth = UserAuth(db)
    #recipe_manager = RecipeManager(db)
    #user_plan_manager = UserPlanManager(db)
    #shopping_list_service = ShoppingListService(user_plan_manager, recipe_manager)

    # Dodajemy serwisy do konfiguracji aplikacji
    #app.config['services'] = {
        #'user_auth': user_auth,
        #'recipe_manager': recipe_manager,
        #'user_plan_manager': user_plan_manager,
        #'shopping_list_service': shopping_list_service
    #}

    # Rejestracja blueprintów
    #from .index import main_bp  # Dodaj ten import
    #from .auth_resource import auth_bp
    #from .recipe_resource import recipes_bp
    #from .plan_resource import plans_bp

    #app.register_blueprint(main_bp)  # Dodaj tę linię
    #app.register_blueprint(auth_bp, url_prefix='/auth')
    #app.register_blueprint(recipes_bp, defaults={'recipe_manager': recipe_manager})
    #app.register_blueprint(plans_bp, defaults={'user_plan_manager': user_plan_manager, 'shopping_list_service': shopping_list_service})

    #return app#



