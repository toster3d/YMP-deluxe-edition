from typing import Any
from datetime import datetime, date
from src.helpers.ingredient_parser import parse_ingredients
from src.helpers.date_range_generator import generate_date_list
from src.services.user_plan_manager import SqliteUserPlanManager
from src.services.recipe_manager import RecipeManager
import logging


class ShoppingListService:
    def __init__(self, user_plan_manager: SqliteUserPlanManager, recipe_manager: RecipeManager) -> None:
        self.user_plan_manager: SqliteUserPlanManager = user_plan_manager
        self.recipe_manager: RecipeManager = recipe_manager

    def get_ingredients_for_date_range(self, user_id: int, date_range: tuple[datetime, datetime]) -> list[str]:
        start_date, end_date = date_range
        ingredients: set[str] = set()
        date_list: list[date] = generate_date_list(start_date, end_date)
        
        for current_date in date_list:
            user_plans: list[dict[str, Any]] = self.user_plan_manager.get_plans(
                user_id, datetime.combine(current_date, datetime.min.time())
            )
            if not user_plans:
                logging.info(f"No plans found for user {user_id} on {current_date}.")
                continue

            meal_names: list[str] = self._get_meal_names(user_plans[0])
            ingredients.update(self._get_ingredients_for_meals(user_id, meal_names))

        if not ingredients:
            logging.warning(f"No ingredients found for user {user_id} in the date range {start_date} to {end_date}.")
            return []

        return list(ingredients)

    def _get_meal_names(self, user_plan: dict[str, str]) -> list[str]:
        return [
            user_plan.get(meal, '')
            for meal in ['breakfast', 'lunch', 'dinner', 'dessert']
            if user_plan.get(meal)
        ]

    def _get_ingredients_for_meals(self, user_id: int, meal_names: list[str]) -> set[str]:
        ingredients: set[str] = set()
        for meal_name in meal_names:
            recipe = self.recipe_manager.get_recipe_by_name(user_id, meal_name)
            if recipe and 'ingredients' in recipe:
                ingredients.update(parse_ingredients(recipe['ingredients']))  # Using the helper function
        return ingredients
