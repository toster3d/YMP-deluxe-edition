from typing import Any, cast
from flask import request, jsonify, make_response, current_app, Response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore
from datetime import datetime, date
from services.user_plan_manager import SqliteUserPlanManager
from flask_sqlalchemy import SQLAlchemy


class ScheduleResource(Resource): # type: ignore
    user_plan_manager: SqliteUserPlanManager
    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required() # type: ignore
    def get(self) -> Response:
        user_id = get_jwt_identity()
        date_str = request.args.get('date', datetime.now().strftime("%A %d %B %Y"))

        try:
            selected_date: date = datetime.strptime(date_str, "%A %d %B %Y").date()
            user_plans = self.user_plan_manager.get_plans(user_id, selected_date)

            response_data: dict[str, Any] = {
                "date": date_str,
                "user_plans": {
                    "user_id": user_id,
                    "breakfast": user_plans.get("breakfast"),
                    "lunch": user_plans.get("lunch"),
                    "dinner": user_plans.get("dinner"),
                    "dessert": user_plans.get("dessert"),
                }
            }

            return make_response(jsonify(response_data), 200)
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)


class ChooseMealResource(Resource): # type: ignore
    user_plan_manager: SqliteUserPlanManager
    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required() #type: ignore
    def get(self) -> Response:
        user_id = get_jwt_identity()
        recipes = self.user_plan_manager.get_user_recipes(user_id)
        return make_response(jsonify({'recipes': recipes}), 200)

    @jwt_required() # type: ignore
    def post(self) -> Response:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        selected_date = data.get('selected_date')
        recipe_id = data.get('recipe_id')
        meal_type = data.get('meal_type')

        if selected_date is None or recipe_id is None or meal_type is None or recipe_id <= 0:
            return make_response(jsonify({"message": "Missing required fields or invalid values"}), 400)

        try:
            selected_date_obj = datetime.strptime(selected_date, "%A %d %B %Y")
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

        try:
            updated_plan = self.user_plan_manager.create_or_update_plan(
                user_id, selected_date_obj, recipe_id, meal_type
            )
            return make_response(jsonify({
                "message": "Meal plan updated successfully!",
                **updated_plan
            }), 200)
        except ValueError as e:
            current_app.logger.warning(f"ValueError occurred: {e}")
            return make_response(jsonify({"message": "Invalid input provided."}), 400)
        except Exception as e:
            current_app.logger.error(f"Error updating meal plan: {str(e)}")
            return make_response(jsonify({"message": "An error occurred while updating the meal plan"}), 500)
