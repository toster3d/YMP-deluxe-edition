from flask import Flask
from flask_restful import Api
from src.resources.auth_resource import AuthResource, RegisterResource, LogoutResource
from src.resources.shopping_list_resource import ShoppingListResource
from src.resources.recipe_resource import RecipeListResource, RecipeResource
from src.resources.plan_resource import ScheduleResource, ChooseMealResource


def register_routes(app: Flask, api: Api) -> None:
    # Register Flask routes for login and registration
    app.add_url_rule(
        '/auth/login',
        'auth.login',
        AuthResource.as_view('login'),
        methods=['GET', 'POST']
    )
    app.add_url_rule(
        '/auth/register',
        'auth.register',
        RegisterResource.as_view('register'),
        methods=['GET', 'POST']
    )
    app.add_url_rule(
        '/auth/logout',
        'auth.logout',
        LogoutResource.as_view('logout'),
        methods=['POST']
    )

    # Register remaining resources
    api.add_resource(RecipeListResource, '/recipes')  # type: ignore
    api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')  # type: ignore
    api.add_resource(ScheduleResource, '/schedule')  # type: ignore
    api.add_resource(ChooseMealResource, '/choose_meal')  # type: ignore
    api.add_resource(ShoppingListResource, '/shopping_list')  # type: ignore