from typing import Any
from flask_restful import Resource
from flask import current_app, jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.recipe_manager import RecipeManager
from .schemas import RecipeSchema
from marshmallow import ValidationError
from flask.wrappers import Response


class RecipeListResource(Resource):
    def __init__(self) -> None:
        self.recipe_manager = RecipeManager(current_app.config['db'])
        self.schema = RecipeSchema()

    @jwt_required()
    def get(self) -> Response:
        user_id: int = get_jwt_identity()
        current_app.logger.info(f"Attempting to get recipes for user ID: {user_id}")

        recipes: list[dict[str, Any]] = self.recipe_manager.get_recipes(user_id)

        if not recipes:
            current_app.logger.info(f"No recipes found for user ID: {user_id}")
            return make_response(jsonify({"message": "No recipes found for this user."}), 404)

        return make_response(jsonify(recipes), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id: int = get_jwt_identity()
        current_app.logger.info(f"Attempting to add recipe for user ID: {user_id}")

        json_data: Any = request.get_json()
        if not json_data:
            current_app.logger.warning("No input data provided")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            data: Any = self.schema.load(json_data)
            current_app.logger.info(f"Validated data: {data}")
        except ValidationError as err:
            current_app.logger.error(f"Validation error: {err.messages}")
            return make_response(jsonify(err.messages), 422)

        try:
            self.recipe_manager.add_recipe(
                user_id,
                data["meal_name"],
                data["meal_type"],
                data["ingredients"],
                data["instructions"]
            )
            current_app.logger.info("Recipe added successfully")
            return make_response(jsonify({"message": "Recipe added successfully!"}), 201)
        except Exception as e:
            current_app.logger.error(f"Error adding recipe: {e}")
            return make_response(jsonify({"message": "Failed to add recipe"}), 500)


class RecipeResource(Resource):
    def __init__(self) -> None:
        self.recipe_manager = RecipeManager(current_app.config['db'])
        self.schema = RecipeSchema()

    @jwt_required()
    def get(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        recipe: Any = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)

        if recipe:
            return make_response(jsonify(recipe), 200)

        current_app.logger.info(f"Recipe with ID {recipe_id} not found for user_id {user_id}.")
        return make_response(jsonify({"message": "Recipe not found"}), 404)

    @jwt_required()
    def delete(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        try:
            self.recipe_manager.delete_recipe(recipe_id, user_id)
            return make_response(jsonify({"message": "Recipe deleted successfully!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error deleting recipe: {e}")
            return make_response(jsonify({"message": str(e)}), 404)

    @jwt_required()
    def put(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        json_data: Any = request.get_json()
        if not json_data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            data: Any = self.schema.load(json_data)
        except ValidationError as err:
            return make_response(jsonify(err.messages), 422)

        try:
            self.recipe_manager.update_recipe(
                recipe_id,
                user_id,
                data["meal_name"],
                data["meal_type"],
                data["ingredients"],
                data["instructions"]
            )
            return make_response(jsonify({"message": "Recipe updated successfully!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error updating recipe: {e}")
            return make_response(jsonify({"message": str(e)}), 404)
