from datetime import date, datetime
from typing import Any, cast

from flask import Response, current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required  # type: ignore
from flask_restful import Resource
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError

from services.user_plan_manager import SqliteUserPlanManager

from .pydantic_schemas import PlanSchema


class ScheduleResource(Resource):
    user_plan_manager: SqliteUserPlanManager

    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required()
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


class ChooseMealResource(Resource):
    user_plan_manager: SqliteUserPlanManager

    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.user_plan_manager = SqliteUserPlanManager(db)

    @jwt_required()
    def get(self) -> Response:
        user_id = get_jwt_identity()
        recipes = self.user_plan_manager.get_user_recipes(user_id)
        return make_response(jsonify({'recipes': recipes}), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id = get_jwt_identity()
        json_data: dict[str, Any] | None = request.get_json()

        if not json_data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            plan_data = PlanSchema(**json_data)
            selected_date_obj = datetime.strptime(plan_data.selected_date.strftime("%A %d %B %Y"), "%A %d %B %Y")
        except ValidationError as err:
            current_app.logger.warning(f"Validation error: {err.errors()}")
            return make_response(jsonify({"message": "Invalid input data.", "errors": err.errors()}), 400)
        except TypeError:
            return make_response(jsonify({"message": "Invalid date format"}), 400)

        try:
            updated_plan = self.user_plan_manager.create_or_update_plan(
                user_id, selected_date_obj, plan_data.recipe_id, plan_data.meal_type
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
