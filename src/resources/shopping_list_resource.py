from typing import cast, Any
from flask import jsonify, request, current_app, Response, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore
from datetime import datetime
from services.shopping_list_service import ShoppingListService
from services.recipe_manager import RecipeManager
from services.user_plan_manager import SqliteUserPlanManager
from flask_sqlalchemy import SQLAlchemy
from .pydantic_schemas import DateRangeSchema
from pydantic import ValidationError


class ShoppingListResource(Resource):
    recipe_manager: RecipeManager
    user_plan_manager: SqliteUserPlanManager
    shopping_list_service: ShoppingListService

    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config["db"])
        self.recipe_manager = RecipeManager(db)
        self.user_plan_manager = SqliteUserPlanManager(db)
        self.shopping_list_service = ShoppingListService(
            self.user_plan_manager, self.recipe_manager
        )

    @jwt_required()     
    def get(self) -> Response:
        user_id = get_jwt_identity()
        current_app.logger.info(f"Fetching shopping list for user_id: {user_id}")
        now: datetime = datetime.now()

        ingredients = self.shopping_list_service.get_ingredients_for_date_range(user_id, (now, now))
        if not ingredients:
            return make_response(jsonify({"message": "No meal plan for today. Check your schedule."}), 404)

        return make_response(jsonify({"ingredients": list(ingredients), "current_date": now.isoformat()}), 200)

    @jwt_required()        
    def post(self) -> Response:
        user_id = get_jwt_identity()
        json_data: dict[str, Any] | None = request.get_json()

        if not json_data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            date_range_data = DateRangeSchema(**json_data)
            start_date_str, end_date_str = date_range_data.date_range.split(" to ")
            start_date = datetime.strptime(start_date_str, "%A %d %B %Y")
            end_date = datetime.strptime(end_date_str, "%A %d %B %Y")
        except ValidationError as err:
            return make_response(jsonify({"message": "Invalid input data.", "errors": err.errors()}), 400)
        except ValueError:
            return make_response(jsonify({"message": 'Invalid date range format. Use "Day Month Year to Day Month Year."'}), 400)

        ingredients = self.shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        if not ingredients:
            return make_response(jsonify({"message": "No meal plan for this date range."}), 404)

        return make_response(jsonify({"ingredients": list(ingredients), "date_range": date_range_data.date_range}), 200)