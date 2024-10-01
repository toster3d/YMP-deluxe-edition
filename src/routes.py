from .resources.auth_resource import AuthResource, RegisterResource, logout
from .resources.shopping_list_resource import ShoppingListResource
from .resources.recipe_resource import RecipeListResource, RecipeResource
from .resources.plan_resource import ScheduleResource, ChooseMealResource
from .resources.index import main_bp

def register_routes(app, api):
    # Register blueprint
    app.register_blueprint(main_bp) # type: ignore

    # Register Flask routes for login and registration
    app.add_url_rule('/auth/login', 'auth.login', AuthResource.as_view('login'), methods=['GET', 'POST'])
    app.add_url_rule('/auth/register', 'auth.register', RegisterResource.as_view('register'), methods=['GET', 'POST'])
    app.add_url_rule('/auth/logout', 'auth.logout', logout, methods=['GET'])

    # Register remaining resources
    api.add_resource(RecipeListResource, '/recipes')
    api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')
    api.add_resource(ScheduleResource, '/schedule')
    api.add_resource(ChooseMealResource, '/choose_meal')
    api.add_resource(ShoppingListResource, '/shopping_list')