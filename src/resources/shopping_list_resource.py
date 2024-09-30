from flask import request, session, current_app
from flask_restful import Resource
from datetime import datetime
from ..helpers.login_required_decorator import login_required

class ShoppingListResource(Resource):
    @login_required
    def get(self):
        user_id = session["user_id"]
        now = datetime.now()
        shopping_list_service = current_app.config['services']['shopping_list_service']
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (now, now))
        if not ingredients:
            return {'message': 'Brak planu posiłków na dziś. Sprawdź swój harmonogram.'}, 404
        return {'ingredients': ingredients, 'current_date': now.strftime("%A %d %B %Y")}, 200

    @login_required
    def post(self):
        user_id = session["user_id"]
        date_range = request.form.get("date_range")
        if not date_range:
            return {'message': 'Musisz wybrać zakres dat.'}, 400
        
        start_date, end_date = date_range.split(" do ")
        start_date = datetime.strptime(start_date, "%A %d %B %Y")
        end_date = datetime.strptime(end_date, "%A %d %B %Y")
        
        shopping_list_service = current_app.config['services']['shopping_list_service']
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        if not ingredients:
            return {'message': 'Brak planu posiłków dla tego zakresu dat.'}, 404

        return {'ingredients': ingredients, 'date_range': date_range}, 200