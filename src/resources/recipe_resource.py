from typing import Any
from flask_restful import Resource
from flask import current_app, jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore
from services.recipe_manager import RecipeManager
from services.recipe_manager import RecipeDict
from .schemas import RecipeSchema, RecipeUpdateSchema
from marshmallow import ValidationError
from flask.wrappers import Response


class RecipeListResource(Resource): 
    def __init__(self) -> None:
        self.recipe_manager: RecipeManager = RecipeManager(current_app.config['db'])
        self.schema: RecipeSchema = RecipeSchema()

    @jwt_required()
    def get(self) -> Response:
        user_id: int = get_jwt_identity()
        current_app.logger.info(f"Attempting to get recipes for user ID: {user_id}")

        recipes: list[RecipeDict] | None = self.recipe_manager.get_recipes(user_id)

        if not recipes:
            current_app.logger.info(f"No recipes found for user ID: {user_id}")
            return make_response(jsonify({"message": "No recipes found for this user."}), 404)

        return make_response(jsonify(recipes), 200)

    @jwt_required()
    def post(self) -> Response:
        user_id: int = get_jwt_identity()
        current_app.logger.info(f"Attempting to add recipe for user ID: {user_id}")

        json_data: dict[str, Any] | None = request.get_json()
        if not json_data:
            current_app.logger.warning("No input data provided")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        try:
            recipe_data: dict[str, Any] = self.schema.load(json_data)  # type: ignore
            current_app.logger.info(f"Validated data: {recipe_data}")
        except ValidationError as err:
            current_app.logger.error(f"Validation error: {err.messages}")  # type: ignore
            return make_response(jsonify(err.messages), 422)  # type: ignore

        try:
            self.recipe_manager.add_recipe(user_id, 
                meal_name=recipe_data["meal_name"],
                meal_type=recipe_data["meal_type"],
                ingredients=recipe_data["ingredients"],
                instructions=recipe_data["instructions"]
            )
            current_app.logger.info("Recipe added successfully")
            return make_response(jsonify({
                "message": "Recipe added successfully!",
                "meal_name": recipe_data["meal_name"],
                "meal_type": recipe_data["meal_type"]
            }), 201)
        except Exception as e:
            current_app.logger.error(f"Error adding recipe: {e}")
            return make_response(jsonify({"message": "Failed to add recipe"}), 500)


class RecipeResource(Resource):
    def __init__(self) -> None:
        self.recipe_manager: RecipeManager = RecipeManager(current_app.config['db'])
        self.schema: RecipeSchema = RecipeSchema()

    @jwt_required()
    def get(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        recipe: RecipeDict | None = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)

        if recipe:
            return make_response(jsonify(recipe), 200)

        current_app.logger.info(f"Recipe with id {recipe_id} not found for user_id {user_id}.")
        return make_response(jsonify({"message": "Recipe not found"}), 404)

    @jwt_required()
    def delete(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        try:
            recipe: RecipeDict | None = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
            if not recipe:
                return make_response(jsonify({"message": "Recipe not found"}), 404)

            self.recipe_manager.delete_recipe(recipe_id, user_id)
            current_app.logger.info(f"Recipe with ID {recipe_id} deleted successfully.")
            return make_response("", 204)
        except Exception as e:
            current_app.logger.error(f"Error deleting recipe: {e}")
            return make_response(jsonify({"message": str(e)}), 404)

    @jwt_required()
    def patch(self, recipe_id: int) -> Response:
        user_id: int = get_jwt_identity()
        json_data: dict[str, Any] | None = request.get_json()
        if not json_data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema = RecipeUpdateSchema()
        try:
            validated_data: dict[str, Any] = schema.load(json_data)  # type: ignore 
            self.recipe_manager.update_recipe(
                recipe_id,
                user_id,
                meal_name=validated_data.get("meal_name"),
                meal_type=validated_data.get("meal_type"),
                ingredients=validated_data.get("ingredients"),
                instructions=validated_data.get("instructions")
            )

            updated_recipe: RecipeDict | None = self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
            
            current_app.logger.info(f"Recipe with ID {recipe_id} updated successfully.")
    
            return make_response(jsonify(updated_recipe), 200)
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 400)  # type: ignore
        except Exception as e:
            current_app.logger.error(f"Error updating recipe: {e}")
            return make_response(jsonify({"message": str(e)}), 404)
