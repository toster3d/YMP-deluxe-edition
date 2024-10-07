from typing import Any
from flask_restful import Resource
from flask import Response, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore
from src.services.recipe_manager import RecipeManager
from .schemas import RecipeSchema
from marshmallow import ValidationError

class RecipeListResource(Resource):
    def __init__(self) -> None:
        self.recipe_manager = RecipeManager(current_app.config['db'])
        self.schema = RecipeSchema()

    @jwt_required()
    def get(self) -> tuple[Response, int]:
        user_id: int = get_jwt_identity()
        recipes: list[dict[str, Any]] = self.recipe_manager.get_recipes(user_id)
        return jsonify(recipes), 200

    @jwt_required()
    def post(self) -> tuple[Response, int]:
        user_id: int = get_jwt_identity()
        json_data: Any = request.get_json()
        if not json_data:
            return jsonify({"message": "No input data provided"}), 400
        
        try:
            data: Any = self.schema.load(json_data)
        except ValidationError as err:
            return jsonify(err.messages), 422 # type: ignore

        try:
            self.recipe_manager.add_recipe(
                user_id,
                data["mealName"],
                data["mealType"],
                data["ingredients"],
                data["instructions"]
            )
            return jsonify({"message": "Recipe added successfully!"}), 201
        except Exception as e:
            return jsonify({"message": str(e)}), 400

class RecipeResource(Resource):
    def __init__(self):
        self.recipe_manager = RecipeManager(current_app.config['db'])
        self.schema = RecipeSchema()

    @jwt_required()
    def get(self, recipe_id: int) -> tuple[Response, int]:
        user_id: int = get_jwt_identity()
        recipe: Any = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
        
        if recipe:
            return jsonify(recipe), 200
        return jsonify({"message": "Recipe not found"}), 404

    @jwt_required()
    def delete(self, recipe_id: int) -> tuple[Response, int]:
        user_id: int = get_jwt_identity()
        try:
            self.recipe_manager.delete_recipe(recipe_id, user_id)
            return jsonify({"message": "Recipe deleted successfully!"}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 404

    @jwt_required()
    def put(self, recipe_id: int) -> tuple[Response, int]:
        user_id: int = get_jwt_identity()
        json_data: Any = request.get_json()
        if not json_data:
            return jsonify({"message": "No input data provided"}), 400
        
        try:
            data: Any = self.schema.load(json_data)
        except ValidationError as err:
            return jsonify(err.messages), 422 # type: ignore

        try:
            self.recipe_manager.update_recipe(
                recipe_id,
                user_id,
                data["mealName"],
                data["mealType"],
                data["ingredients"],
                data["instructions"]
            )
            return jsonify({"message": "Recipe updated successfully!"}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 404
