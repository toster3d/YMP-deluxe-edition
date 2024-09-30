from flask import request, session, current_app
from flask_restful import Resource
from datetime import datetime
from ..helpers.login_required_decorator import login_required

class ScheduleResource(Resource):
    @login_required
    def get(self):
        user_id = session["user_id"]
        date = request.args.get('date')
        if not date:
            now = datetime.now()
            date = now.strftime("%A %d %B %Y")
        user_plan_manager = current_app.config['services']['user_plan_manager']
        user_plans = user_plan_manager.get_plans(user_id, date)
        return {'date': date, 'userPlans': user_plans}, 200

    @login_required
    def post(self):
        user_id = session["user_id"]
        date = request.form.get("date")
        selected_date = request.form.get("selected_date")
        user_plan_manager = current_app.config['services']['user_plan_manager']
        if selected_date:
            user_plan_manager.update_plan(user_id, selected_date)
            return {"message": "Plan updated successfully!"}, 200
        else:
            user_plans = user_plan_manager.get_plans(user_id, date)
            return {'userPlans': user_plans}, 200


class ChooseMealResource(Resource):
    @login_required
    def get(self):
        user_id = session["user_id"]
        recipe_manager = current_app.config['services']['recipe_manager']
        items = recipe_manager.get_recipes_ordered_by_meal_type(user_id)
        return {'items': items}, 200

    @login_required
    def post(self):
        user_id = session["user_id"]
        selected_date = request.form.get('selected_date')
        user_plan = request.form["userPlan"]
        meal_name = request.form.get("mealName")
        user_plan_manager = current_app.config['services']['user_plan_manager']
        user_plan_manager.create_or_update_plan(user_id, selected_date, user_plan, meal_name)
        return {"message": "Meal plan created or updated!"}, 201
