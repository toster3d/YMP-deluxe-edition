from flask import Flask, render_template
from flask_restful import Api
from . import create_app, configure_app, db  # Dodaj import db
from .resources.auth_resource import AuthResource, RegisterResource, login, register
from .resources.shopping_list_resource import ShoppingListResource
from .resources.recipe_resource import RecipeListResource, RecipeResource
from .resources.plan_resource import ScheduleResource, ChooseMealResource
from .resources.index import main_bp  # Dodaj ten import

app = create_app()
configure_app(app)
api = Api(app)

# Rejestracja blueprintu
app.register_blueprint(main_bp)  # Dodaj tę linię

# Rejestracja standardowych tras Flask dla logowania i rejestracji
app.add_url_rule('/auth/login', 'auth.login', login, methods=['GET', 'POST'])
app.add_url_rule('/auth/register', 'auth.register', register, methods=['GET', 'POST'])

# Rejestracja pozostałych zasobów
api.add_resource(RecipeListResource, '/recipes')
api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')
api.add_resource(ScheduleResource, '/schedule')
api.add_resource(ChooseMealResource, '/chooseMeal')
api.add_resource(ShoppingListResource, '/shoppingList')

# Usuń tę trasę, ponieważ jest już obsługiwana przez blueprint
# @app.route('/')
# def index():
#     return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
