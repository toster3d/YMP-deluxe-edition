from datetime import datetime
from typing import List, Tuple
from .date_range_generator import DateRangeGenerator
from .ingredient_parser import IngredientParser


class ShoppingListService:
    """
    A service class for managing shopping lists based on user meal plans and recipes.
    """

    def __init__(self, user_plan_manager, recipe_manager):
        """
        Initialize the ShoppingListService with necessary dependencies.

        Args:
            user_plan_manager: An instance of the user plan manager.
            recipe_manager: An instance of the recipe manager.
        """
        self.user_plan_manager = user_plan_manager
        self.recipe_manager = recipe_manager
        self.date_range_generator = DateRangeGenerator()
        self.ingredient_parser = IngredientParser()

    def get_ingredients_for_date_range(self, user_id: int, date_range: Tuple[datetime, datetime]) -> List[str]:
        """
        Retrieve a list of unique ingredients for a user's meal plans within a specified date range.

        Args:
            user_id (int): The ID of the user.
            date_range (Tuple[datetime, datetime]): A tuple containing the start and end dates.

        Returns:
            List[str]: A list of unique ingredients required for the meal plans.
        """
        start_date, end_date = date_range
        ingredients = []
        date_list = self.date_range_generator.generate_date_list(start_date, end_date)

        for date in date_list:
            user_plans = self.user_plan_manager.get_plans(user_id, date.strftime("%A %d %B %Y"))
            if user_plans:
                meal_names = [
                    user_plans[0][meal]
                    for meal in ['breakfast', 'lunch', 'dinner', 'dessert']
                    if user_plans[0][meal]
                ]
                for meal_name in meal_names:
                    recipe = self.recipe_manager.get_recipe_by_name(user_id, meal_name)
                    if recipe:
                        ingredients.extend(
                            self.ingredient_parser.parse_ingredients(recipe['ingredients'])
                        )

        return list(set(ingredients))
