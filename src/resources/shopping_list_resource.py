from typing import Literal, Union
from flask import jsonify, request, current_app, Response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore
from datetime import datetime
from src.services.shopping_list_service import ShoppingListService
from src.services.recipe_manager import RecipeManager
from src.services.user_plan_manager import SqliteUserPlanManager


class ShoppingListResource(Resource):
    def __init__(self) -> None:
        self.recipe_manager = RecipeManager(current_app.config["db"])
        self.user_plan_manager = SqliteUserPlanManager(current_app.config["db"])
        self.shopping_list_service = ShoppingListService(self.user_plan_manager, self.recipe_manager)

    @jwt_required()
    def get(self) -> Union[tuple[Response, Literal[404]], tuple[Response, Literal[200]]]:
        user_id: int = get_jwt_identity()
        now: datetime = datetime.now()

        ingredients: list[str] = self.shopping_list_service.get_ingredients_for_date_range(user_id, (now, now))
        if not ingredients:
            return jsonify({"message": "No meal plan for today. Check your schedule."}), 404

        return jsonify({"ingredients": ingredients, "current_date": now.isoformat()}), 200

    @jwt_required()
    def post(self) -> Union[tuple[Response, Literal[400]], tuple[Response, Literal[404]], tuple[Response, Literal[200]]]:
        user_id: int = get_jwt_identity()
        date_range: str | None = request.form.get("date_range")
        if not date_range:
            return jsonify({"message": "You must select a date range."}), 400

        try:
            start_date_str, end_date_str = date_range.split(" to ")
            start_date: datetime = datetime.strptime(start_date_str, "%A %d %B %Y")
            end_date: datetime = datetime.strptime(end_date_str, "%A %d %B %Y")
        except ValueError:
            return jsonify({"message": 'Invalid date range format. Use "Day Month Year to Day Month Year."'}), 400

        ingredients: list[str] = self.shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        if not ingredients:
            return jsonify({"message": "No meal plan for this date range."}), 404

        return jsonify({"ingredients": ingredients, "date_range": date_range}), 200