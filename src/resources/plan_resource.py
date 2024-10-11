from typing import Any
from flask import request, jsonify, make_response, current_app, Response            
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from src.services.user_plan_manager import SqliteUserPlanManager
from src.extensions import db

class ScheduleResource(Resource):
    def __init__(self) -> None:
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required()
    def get(self) -> Response:
        user_id = get_jwt_identity()
        date_str = request.args.get('date', datetime.now().strftime("%A %d %B %Y"))

        try:
            selected_date = datetime.strptime(date_str, "%A %d %B %Y").date()
            user_plans = self.user_plan_manager.get_plans(user_id, selected_date)

            return make_response(jsonify({'date': date_str, 'user_plans': user_plans}), 200)
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

class ChooseMealResource(Resource):
    def __init__(self) -> None:
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required()
    def get(self) -> Response:
        user_id: int = get_jwt_identity()
        recipes = self.user_plan_manager.get_user_recipes(user_id)
        return make_response(jsonify({'recipes': recipes}), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id: int = get_jwt_identity()
        data = request.get_json()

        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        selected_date: str = data.get('selected_date', '')
        recipe_id: int = data.get('recipe_id')
        meal_type: str = data.get('meal_type', '')

        if not selected_date or recipe_id is None or not meal_type:
            return make_response(jsonify({"message": "Missing required fields"}), 400)

        try:
             selected_date_obj = datetime.strptime(selected_date, "%A %d %B %Y").date()
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

        try:
            updated_plan = self.user_plan_manager.create_or_update_plan(user_id, selected_date_obj, recipe_id, meal_type)
            return make_response(jsonify({"message": "Meal plan updated successfully!", "plan": str(updated_plan)}), 200)
        except ValueError as e:
            return make_response(jsonify({"message": str(e)}), 400)
        except Exception as e:
            current_app.logger.error(f"Error updating meal plan: {str(e)}")
            return make_response(jsonify({"message": "An error occurred while updating the meal plan"}), 500)
