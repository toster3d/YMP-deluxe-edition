from datetime import datetime, timedelta

class ShoppingListService:
    def __init__(self, user_plan_manager, recipe_manager):
        self.user_plan_manager = user_plan_manager
        self.recipe_manager = recipe_manager

    def get_ingredients_for_date_range(self, user_id, date_range):
        start_date, end_date = date_range
        ingredients = []
        date_list = self._generate_date_list(start_date, end_date)

        for date in date_list:
            user_plans = self.user_plan_manager.get_plans(user_id, date.strftime("%A %d %B %Y"))
            if user_plans:
                meal_names = [user_plans[0][meal] for meal in ['breakfast', 'lunch', 'dinner', 'dessert'] if user_plans[0][meal]]
                for meal_name in meal_names:
                    recipe = self.recipe_manager.get_recipe_by_name(user_id, meal_name)
                    if recipe:
                        ingredients.extend(self._parse_ingredients(recipe['ingredients']))

        return list(set(ingredients))  # Usuwamy duplikaty

    def _generate_date_list(self, start_date, end_date):
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        return date_list

    def _parse_ingredients(self, ingredients_string):
        return [ing.strip() for ing in ingredients_string.split("\n") if ing.strip()]
