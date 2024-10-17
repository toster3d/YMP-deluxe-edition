from flask import Flask
from flask_restful import Api
from src.resources.auth_resource import AuthResource, RegisterResource, LogoutResource
from src.resources.shopping_list_resource import ShoppingListResource
from src.resources.recipe_resource import RecipeListResource, RecipeResource
from src.resources.plan_resource import ScheduleResource, ChooseMealResource


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

    api.add_resource(RecipeListResource, '/recipe')  
    api.add_resource(RecipeResource, '/recipe/<int:recipe_id>')  
    api.add_resource(ScheduleResource, '/schedule')  
    api.add_resource(ChooseMealResource, '/meal_plan')  
    api.add_resource(ShoppingListResource, '/shopping_list') 
    api.add_resource(RegisterResource, '/auth/register')
