from typing import Any, Literal
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from src.services.recipe_manager import RecipeManager

class ScheduleResource(Resource):
    @jwt_required()
    def get(self) -> tuple[dict[str, str | Any], Literal[200]]:
        user_id: str = get_jwt_identity()
        date: str | None = request.args.get('date')
        if not date:
            now: datetime = datetime.now()
            date = now.strftime("%A %d %B %Y")

        user_plan_manager = current_app.config['services']['user_plan_manager']
        user_plans = user_plan_manager.get_plans(user_id, date)
        return {'date': date, 'user_plans': user_plans}, 200

    @jwt_required()
    def post(self) -> tuple[dict[str, str], int]:
        user_id: str = get_jwt_identity()
        date: str | None = request.form.get("date")
        selected_date: str | None = request.form.get("selected_date")
        user_plan_manager = current_app.config['services']['user_plan_manager']
        
        if selected_date:
            user_plan_manager.update_plan(user_id, selected_date)
            return {"message": "Plan updated successfully!"}, 200
        
        user_plans = user_plan_manager.get_plans(user_id, date)
        return {'user_plans': user_plans}, 200

class ChooseMealResource(Resource):
    @jwt_required()
    def get(self) -> tuple[dict[str, list[dict]], int]:
        user_id: str = get_jwt_identity()
        recipe_manager: RecipeManager = current_app.config['services']['recipe_manager']
        items = recipe_manager.get_recipes_ordered_by_meal_type(user_id)
        return {'items': items}, 200

    @jwt_required()
    def post(self) -> tuple[dict[str, str], int]:
        user_id: str = get_jwt_identity()
        selected_date: str = request.form.get('selected_date')
        user_plan: str = request.form["userPlan"]
        meal_name: str | None = request.form.get("mealName")
        user_plan_manager = current_app.config['services']['user_plan_manager']
        
        user_plan_manager.create_or_update_plan(user_id, selected_date, user_plan, meal_name)
        return {"message": "Meal plan created or updated!"}, 201
