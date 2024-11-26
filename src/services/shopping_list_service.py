import logging
from datetime import date
from typing import Generator

from helpers.date_range_generator import generate_date_list
from services.recipe_manager import AbstractRecipeManager
from services.user_plan_manager import AbstractUserPlanManager


class ShoppingListService:
    user_plan_manager: AbstractUserPlanManager
    recipe_manager: AbstractRecipeManager

    def __init__(self, user_plan_manager: AbstractUserPlanManager, recipe_manager: AbstractRecipeManager) -> None:
        self.user_plan_manager = user_plan_manager
        self.recipe_manager = recipe_manager

    def get_ingredients_for_date_range(self, user_id: int, date_range: tuple[date, date]) -> set[str]:
        start_date, end_date = date_range
        ingredients: set[str] = set()
        date_list = generate_date_list(start_date, end_date)

        logging.info(f"Fetching ingredients for user {user_id} from {start_date} to {end_date}")
        for current_date in date_list:
            user_plan = self.user_plan_manager.get_plans(user_id=user_id, date=current_date)
            logging.info(f"User plan for {current_date}: {user_plan}")

            if not user_plan:
                logging.info(f"No plan found for user {user_id} on {current_date}.")
                continue

            meal_names: Generator[str, None, None] = self._get_meal_names(user_plan)

            for meal_name in meal_names:
                new_ingredients: set[str] = self._get_ingredients_for_meals(user_id, [meal_name])
                logging.info(f"Ingredients for {meal_name} on {current_date}: {new_ingredients}")

                ingredients.update(new_ingredients)

        if not ingredients:
            logging.warning(f"No ingredients found for user {user_id} in the date range {start_date} to {end_date}.")
            return set()

        logging.info(f"Final ingredients set: {ingredients}")
        return ingredients

    def _get_meal_names(self, user_plan: dict[str, int | date | str]) -> Generator[str, None, None]:
        for meal in ['breakfast', 'lunch', 'dinner', 'dessert']:
            if (meal_info := user_plan.get(meal)):
                if isinstance(meal_info, str) and (meal_name := self._extract_meal_name(meal_info)):
                    yield meal_name

    def _extract_meal_name(self, meal_info: str) -> str | None:
        if '(ID:' in meal_info:
            return meal_info.split('(ID:')[0].strip()
        return meal_info

    def _get_ingredients_for_meals(self, user_id: int, meal_names: list[str]) -> set[str]:
        ingredients: set[str] = set()
        for meal_name in meal_names:
            if (recipe := self.recipe_manager.get_recipe_by_name(user_id, meal_name)):
                logging.info(f"Recipe for {meal_name}: {recipe}")
                if 'ingredients' in recipe:
                    ingredients.update(recipe['ingredients'])
        return ingredients