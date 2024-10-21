from typing import Any
from flask import request, jsonify, make_response, current_app, Response            
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore
from datetime import datetime, date
from services.user_plan_manager import SqliteUserPlanManager
from flask_sqlalchemy import SQLAlchemy

class ScheduleResource(Resource): 
    def __init__(self) -> None:
        db: SQLAlchemy = current_app.config['db']  # type: ignore
        self.user_plan_manager: SqliteUserPlanManager = SqliteUserPlanManager(db)  # type: ignore

    @jwt_required()
    def get(self) -> Response:
        user_id: int = get_jwt_identity()
        date_str: str = request.args.get('date', datetime.now().strftime("%A %d %B %Y"))

        try:
            selected_date: datetime = datetime.strptime(date_str, "%A %d %B %Y")
            user_plans: dict[str, int | date | str] = self.user_plan_manager.get_plans(user_id, selected_date)

            response_data: dict[str, str | dict[str, int | date | str | None]] = {
                "date": date_str,
                "user_plans": {
                    "user_id": user_id,
                    "breakfast": user_plans.get("breakfast") if user_plans else None,
                    "lunch": user_plans.get("lunch") if user_plans else None,
                    "dinner": user_plans.get("dinner") if user_plans else None,
                    "dessert": user_plans.get("dessert") if user_plans else None,
                }
            }

            return make_response(jsonify(response_data), 200)
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

class ChooseMealResource(Resource):      
    def __init__(self) -> None:
        db: SQLAlchemy = current_app.config['db']  # type: ignore
        self.user_plan_manager: SqliteUserPlanManager = SqliteUserPlanManager(db)  # type: ignore

    @jwt_required()
    def get(self) -> Response:
        user_id: int = get_jwt_identity()
        recipes: list[dict[str, Any]] | None = self.user_plan_manager.get_user_recipes(user_id)
        return make_response(jsonify({'recipes': recipes}), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id: int = get_jwt_identity()
        data: dict[str, Any] | None = request.get_json()

        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        selected_date: str | None = data.get('selected_date')
        recipe_id: int | None = data.get('recipe_id')
        meal_type: str | None = data.get('meal_type')

        if selected_date is None or recipe_id is None or meal_type is None:
            return make_response(jsonify({"message": "Missing required fields"}), 400)

        try:
            selected_date_obj: datetime = datetime.strptime(selected_date, "%A %d %B %Y")
        except ValueError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

        try:
            updated_plan: dict[str, Any] = self.user_plan_manager.create_or_update_plan(user_id, selected_date_obj, recipe_id, meal_type)
            return make_response(jsonify({
                "message": "Meal plan updated successfully!",
                **updated_plan
            }), 200)
        except ValueError as e:
            return make_response(jsonify({"message": str(e)}), 400)
        except Exception as e:
            current_app.logger.error(f"Error updating meal plan: {str(e)}")
            return make_response(jsonify({"message": "An error occurred while updating the meal plan"}), 500)
