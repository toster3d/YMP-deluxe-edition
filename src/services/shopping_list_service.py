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

        logging.info(f"Fetching ingredients for user {user_id} from {start_date} to {end_date}")

        for current_date in date_list:
            user_plan = self.user_plan_manager.get_plans(user_id=user_id, date=datetime.combine(current_date, datetime.min.time()))
            logging.info(f"User plan for {current_date}: {user_plan}")

            if not user_plan:
                logging.info(f"No plan found for user {user_id} on {current_date}.")
                continue

            meal_names = self._get_meal_names(user_plan)
            logging.info(f"Meal names for {current_date}: {meal_names}")

            new_ingredients = self._get_ingredients_for_meals(user_id, meal_names)
            logging.info(f"Ingredients for {current_date}: {new_ingredients}")

            ingredients.update(new_ingredients)

        if not ingredients:
            logging.warning(f"No ingredients found for user {user_id} in the date range {start_date} to {end_date}.")
            return []

        logging.info(f"Final ingredients list: {list(ingredients)}")
        return list(ingredients)

    def _get_meal_names(self, user_plan: dict[str, Any]) -> list[str]:
        meal_names = []
        for meal in ['breakfast', 'lunch', 'dinner', 'dessert']:
            meal_info = user_plan.get(meal)
            if meal_info:
                meal_name = self._extract_meal_name(meal_info)
                if meal_name:
                    meal_names.append(meal_name)
        logging.info(f"Extracted meal names: {meal_names}")
        return meal_names

    def _extract_meal_name(self, meal_info: str) -> str | None:
        if '(ID:' in meal_info:
            return meal_info.split('(ID:')[0].strip()
        return meal_info

    def _get_ingredients_for_meals(self, user_id: int, meal_names: list[str]) -> set[str]:
        ingredients: set[str] = set()
        for meal_name in meal_names:
            recipe = self.recipe_manager.get_recipe_by_name(user_id, meal_name)
            logging.info(f"Recipe for {meal_name}: {recipe}")
            if recipe and 'ingredients' in recipe:
                parsed_ingredients = parse_ingredients(recipe['ingredients'])
                logging.info(f"Parsed ingredients for {meal_name}: {parsed_ingredients}")
                ingredients.update(parsed_ingredients)
        return ingredients