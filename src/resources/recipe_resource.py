from typing import Any, cast

from flask import current_app, jsonify, make_response, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt_identity, jwt_required  # type: ignore
from flask_restful import Resource
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError

from services.recipe_manager import RecipeManager

from .pydantic_schemas import RecipeSchema, RecipeUpdateSchema


class RecipeListResource(Resource):
    recipe_manager: RecipeManager

    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.recipe_manager = RecipeManager(db)

    @jwt_required()
    def get(self) -> Response:
        user_id = get_jwt_identity()
        current_app.logger.info(f"Attempting to get recipes for user ID: {user_id}")

        recipes = self.recipe_manager.get_recipes(user_id)

        if not recipes:
            current_app.logger.info(f"No recipes found for user ID: {user_id}")
            return make_response(jsonify({"message": "No recipes found for this user."}), 404)

        return make_response(jsonify(recipes), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id = get_jwt_identity()
        current_app.logger.info(f"Attempting to add recipe for user ID: {user_id}")

        json_data: dict[str, Any] | None = request.get_json()
        if not json_data:
            current_app.logger.warning("No input data provided")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            recipe_data = RecipeSchema(**json_data)
            current_app.logger.info(f"Validated data: {recipe_data.model_dump()}")
        except ValidationError as err:
            current_app.logger.error(f"Validation error: {err.errors()}")
            return make_response(jsonify(err.errors()), 422)

        try:
            self.recipe_manager.add_recipe(
                user_id,
                meal_name=recipe_data.meal_name,
                meal_type=recipe_data.meal_type,
                ingredients=recipe_data.ingredients,
                instructions=recipe_data.instructions
            )
            current_app.logger.info("Recipe added successfully")
            return make_response(jsonify({
                "message": "Recipe added successfully!",
                "meal_name": recipe_data.meal_name,
                "meal_type": recipe_data.meal_type
            }), 201)
        except Exception as e:
            current_app.logger.error(f"Error adding recipe: {e}")
            return make_response(jsonify({"message": "Failed to add recipe"}), 500)


class RecipeResource(Resource):
    recipe_manager: RecipeManager

    def __init__(self) -> None:
        db = cast(SQLAlchemy, current_app.config['db'])
        self.recipe_manager = RecipeManager(db)

    @jwt_required()
    def get(self, recipe_id: int) -> Response:
        user_id = get_jwt_identity()
        recipe = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)

        if recipe:
            return make_response(jsonify(recipe), 200)

        current_app.logger.info(f"Recipe with id {recipe_id} not found for user_id {user_id}.")
        return make_response(jsonify({"message": "Recipe not found"}), 404)

    @jwt_required()
    def delete(self, recipe_id: int) -> Response:
        user_id = get_jwt_identity()
        try:
            recipe = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
            if recipe is None:
                return make_response(jsonify({"message": "Recipe not found"}), 404)

            self.recipe_manager.delete_recipe(recipe_id, user_id)
            current_app.logger.info(f"Recipe with ID {recipe_id} deleted successfully.")
            return make_response("", 204)
        except Exception as e:
            current_app.logger.error(f"Error deleting recipe: {e}")
            return make_response(jsonify({"message": "Failed to delete recipe."}), 500)

    @jwt_required()
    def patch(self, recipe_id: int) -> Response:
        user_id = get_jwt_identity()
        json_data: dict[str, Any] | None = request.get_json()
        if not json_data:
            current_app.logger.warning("No input data provided")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            validated_data = RecipeUpdateSchema(**json_data)
            self.recipe_manager.update_recipe(
                recipe_id,
                user_id,
                meal_name=validated_data.meal_name,
                meal_type=validated_data.meal_type,
                ingredients=validated_data.ingredients,
                instructions=validated_data.instructions
            )

            updated_recipe = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)

            current_app.logger.info(f"Recipe with ID {recipe_id} updated successfully.")

            return make_response(jsonify(updated_recipe), 200)
        except ValidationError as err:
            return make_response(jsonify({"errors": err.errors()}), 400)
        except Exception as e:
            current_app.logger.error(f"Error updating recipe: {e}")
            return make_response(jsonify({"message": "Failed to update recipe."}), 500)
