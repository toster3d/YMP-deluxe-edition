from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.helpers.login_required_decorator import login_required
from datetime import datetime

class ShoppingListResource(Resource):
    @login_required
    def get(self):
        user_id = session["user_id"]
        now = datetime.now()
        shopping_list_service = current_app.config['services']['shopping_list_service']
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (now, now))
        if not ingredients:
            # Change to: No meal plan for today
            return {'message': 'No meal plan for today. Check your schedule.'}, 404
        return {'ingredients': ingredients, 'current_date': now.strftime("%A %d %B %Y")}, 200

    @login_required
    def post(self):
        user_id = session["user_id"]
        date_range = request.form.get("date_range")
        if not date_range:
            # Change to: You must select a date range
            return {'message': 'You must select a date range.'}, 400
        
        start_date, end_date = date_range.split(" to ")
        start_date = datetime.strptime(start_date, "%A %d %B %Y")
        end_date = datetime.strptime(end_date, "%A %d %B %Y")
        
        shopping_list_service = current_app.config['services']['shopping_list_service']
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        if not ingredients:
            # Change to: No meal plan for this date range
            return {'message': 'No meal plan for this date range.'}, 404

        return {'ingredients': ingredients, 'date_range': date_range}, 200