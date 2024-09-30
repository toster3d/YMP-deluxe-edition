from flask_restful import Resource, reqparse
from flask import current_app, session, jsonify

class RecipeListResource(Resource):
    def get(self):
        if 'user_id' not in session:
            return jsonify({"message": "Użytkownik nie jest zalogowany"}), 401
        recipe_manager = current_app.config['services']['recipe_manager']
        user_id = session['user_id']
        recipes = recipe_manager.get_recipes(user_id)
        return jsonify(recipes)
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("mealName", type=str, required=True)
        parser.add_argument("mealType", type=str, required=True)
        parser.add_argument("ingredients", type=str, required=True)
        parser.add_argument("instructions", type=str, required=True)
        args = parser.parse_args()

        recipe_manager = current_app.config['services']['recipe_manager']
        user_id = session['user_id']
        recipe_manager.add_recipe(user_id, args["mealName"], args["mealType"], args["ingredients"], args["instructions"])
        return jsonify({"message": "Recipe added successfully!"}), 201

class RecipeResource(Resource):
    def get(self, recipe_id):
        recipe_manager = current_app.config['services']['recipe_manager']
        user_id = session['user_id']
        recipe = recipe_manager.get_recipe_by_id(recipe_id, user_id)
        if recipe:
            return jsonify(recipe)
        return jsonify({"message": "Recipe not found"}), 404

    def delete(self, recipe_id):
        recipe_manager = current_app.config['services']['recipe_manager']
        user_id = session['user_id']
        success = recipe_manager.delete_recipe(recipe_id, user_id)
        if success:
            return jsonify({"message": "Recipe deleted successfully!"})
        return jsonify({"message": "Recipe not found"}), 404
