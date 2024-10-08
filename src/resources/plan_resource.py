from typing import Any, Literal
from flask import request, current_app, jsonify
from flask.wrappers import Response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore
from datetime import datetime
from src.services.recipe_manager import RecipeManager
from src.services.user_plan_manager import SqliteUserPlanManager


class ScheduleResource(Resource):
    def __init__(self) -> None:
        self.user_plan_manager = SqliteUserPlanManager(current_app.config['db'])

    @jwt_required()
    def get(self) -> tuple[Response, Literal[200]]:
        user_id: int = get_jwt_identity()

        date: str = request.args.get('date', '')
        if not date:
            now: datetime = datetime.now()
            date = now.strftime("%A %d %B %Y")

        user_plans: list[dict[str, Any]] = self.user_plan_manager.get_plans(
            user_id, datetime.strptime(date, "%A %d %B %Y")
        )

        return jsonify({'date': date, 'user_plans': user_plans}), 200

    @jwt_required()
    def post(self) -> tuple[Response, Literal[400]] | tuple[Response, Literal[201]]:
        user_id: int = get_jwt_identity()

        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        selected_date: str = data.get("selected_date", "")
        user_plan: str = data.get("user_plan", "")
        meal_name: str = data.get("meal_name", "")

        if not selected_date or not user_plan or not meal_name:
            return jsonify({"message": "Missing required fields"}), 400

        try:
            selected_date_obj: datetime = datetime.strptime(selected_date, "%A %d %B %Y")
        except ValueError:
            return jsonify({"message": "Invalid date format"}), 400

        self.user_plan_manager.create_or_update_plan(user_id, selected_date_obj, user_plan, meal_name)

        return jsonify({"message": "Meal plan created or updated!"}), 201


class ChooseMealResource(Resource):
    def __init__(self) -> None:
        self.user_plan_manager = SqliteUserPlanManager(current_app.config['db'])
        self.recipe_manager = RecipeManager(current_app.config['db'])

    @jwt_required()
    def get(self) -> tuple[Response, Literal[200]]:
        user_id: int = get_jwt_identity()
        items: list[dict[str, Any]] = self.recipe_manager.get_recipes_ordered_by_meal_type(user_id)
        return jsonify({'items': items}), 200

    @jwt_required()
    def post(self) -> tuple[Response, Literal[400]] | tuple[Response, Literal[201]]:
        user_id: int = get_jwt_identity()
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        selected_date: str = data.get('selected_date', '')
        user_plan: str = data.get('user_plan', '')
        meal_name: str = data.get('meal_name', '')

        if not selected_date or not user_plan or not meal_name:
            return jsonify({"message": "Missing required fields"}), 400

        try:
            selected_date_obj: datetime = datetime.strptime(selected_date, "%A %d %B %Y")
        except ValueError:
            return jsonify({"message": "Invalid date format"}), 400

        self.user_plan_manager.create_or_update_plan(user_id, selected_date_obj, user_plan, meal_name)
        return jsonify({"message": "Meal plan created or updated!"}), 201
