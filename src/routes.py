from flask import Flask
from flask_restful import Api

from resources.auth_resource import AuthResource, LogoutResource, RegisterResource
from resources.plan_resource import ChooseMealResource, ScheduleResource
from resources.recipe_resource import RecipeListResource, RecipeResource
from resources.shopping_list_resource import ShoppingListResource


def register_routes(app: Flask, api: Api) -> None:
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

    api.add_resource(RecipeListResource, '/recipe')  #type: ignore  
    api.add_resource(RecipeResource, '/recipe/<int:recipe_id>')  #type: ignore
    api.add_resource(ScheduleResource, '/schedule')  #type: ignore
    api.add_resource(ChooseMealResource, '/meal_plan')  #type: ignore
    api.add_resource(ShoppingListResource, '/shopping_list')  #type: ignore
    api.add_resource(RegisterResource, '/auth/register')  #type: ignore
