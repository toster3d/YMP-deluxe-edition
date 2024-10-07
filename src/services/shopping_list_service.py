from datetime import date, datetime
# FIXME: no need
from ..helpers.date_range_generator import generate_date_list
from ..helpers.ingredient_parser import parse_ingredients
from .user_plan_manager import AbstractUserPlanManager
from .recipe_manager import RecipeManager

class ShoppingListService:
    """
    A service class for managing shopping lists based on user meal plans and recipes.
    """

    def __init__(self, user_plan_manager: AbstractUserPlanManager, recipe_manager: RecipeManager):
        """
        Initialize the ShoppingListService with necessary dependencies.

        Args:
            user_plan_manager: An instance of the user plan manager.
            recipe_manager: An instance of the recipe manager.
        """
        self.user_plan_manager = user_plan_manager
        self.recipe_manager = recipe_manager

    def get_ingredients_for_date_range(self, user_id: int, date_range: tuple[datetime, datetime]) -> list[str]:
        """
        Retrieve a list of unique ingredients for a user's meal plans within a specified date range.

        Args:
            user_id (int): The ID of the user.
            date_range (Tuple[datetime, datetime]): A tuple containing the start and end dates.

        Returns:
            List[str]: A list of unique ingredients required for the meal plans.
        """
        start_date, end_date = date_range
        ingredients = [] # FIXME: use set
        date_list: list[date] = generate_date_list(start_date, end_date)

        # FIXME: no nested loops
        for date in date_list:
            user_plans = self.user_plan_manager.get_plans(user_id, date.strftime("%A %d %B %Y"))
            if user_plans:
                meal_names = [
                    # FIXME: Potential KeyError
                    user_plans[0][meal]
                    for meal in ['breakfast', 'lunch', 'dinner', 'dessert']
                    if user_plans[0][meal]
                ]
                for meal_name in meal_names:
                    recipe = self.recipe_manager.get_recipe_by_name(user_id, meal_name)
                    if recipe:
                        ingredients.extend(
                            parse_ingredients(recipe['ingredients'])
                        )

        return list(set(ingredients))
