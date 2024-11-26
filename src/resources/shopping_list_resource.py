from datetime import date, datetime
from typing import Any, cast

from flask import Response, current_app, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required  # type: ignore
from flask_restful import Resource
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError

from services.recipe_manager import RecipeManager
from services.shopping_list_service import ShoppingListService
from services.user_plan_manager import SqliteUserPlanManager

from .pydantic_schemas import DateRangeSchema


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
        now: date = datetime.now().date()

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
            start_date = date_range_data.start_date
            end_date = date_range_data.end_date
        except ValidationError as err:
            return make_response(jsonify({"message": "Invalid input data.", "errors": err.errors()}), 400)

        ingredients = self.shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        if not ingredients:
            return make_response(jsonify({"message": "No meal plan for this date range."}), 404)

        return make_response(jsonify({"ingredients": list(ingredients), "date_range": date_range_data.start_date.isoformat() + " to " + date_range_data.end_date.isoformat()}), 200)