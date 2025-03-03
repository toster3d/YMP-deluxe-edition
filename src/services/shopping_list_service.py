import asyncio
import logging
from datetime import date
from typing import Generator

from helpers.date_range_generator import generate_date_list
from services.recipe_manager import AbstractRecipeManager
from services.user_plan_manager import AbstractUserPlanManager


class ShoppingListService:
    """Service for managing shopping lists."""

    def __init__(
        self,
        user_plan_manager: AbstractUserPlanManager,
        recipe_manager: AbstractRecipeManager,
    ) -> None:
        """Initialize service with plan manager and recipe manager."""
        self.user_plan_manager = user_plan_manager
        self.recipe_manager = recipe_manager

    async def get_ingredients_for_date_range(
        self, user_id: int, date_range: tuple[date, date]
    ) -> set[str]:
        """Get ingredients for meal plans in date range."""
        start_date, end_date = date_range
        ingredients: set[str] = set()
        date_list = generate_date_list(start_date, end_date)

        for current_date in date_list:
            user_plan = await self.user_plan_manager.get_plans(
                user_id=user_id, date=current_date
            )
            
            if not user_plan:
                continue

            meal_names = self._get_meal_names(user_plan)
            for meal_name in meal_names:
                new_ingredients = await self._get_ingredients_for_meals(
                    user_id, [meal_name]
                )
                logging.info(
                    f"Ingredients for {meal_name} on {current_date}: {new_ingredients}"
                )
                ingredients.update(new_ingredients)

        if not ingredients:
            return set()

        logging.info(f"Final ingredients set: {ingredients}")
        return ingredients
    
    def _get_meal_names(
        self, user_plan: dict[str, int | date | str]
    ) -> Generator[str, None, None]:
        """Extract meal names from user plan."""
        # FIXME: refactor
        for meal in ["breakfast", "lunch", "dinner", "dessert"]:
            if meal_info := user_plan.get(meal):
                if isinstance(meal_info, str) and (
                    meal_name := self._extract_meal_name(meal_info)
                ):
                    yield meal_name
        #FIXME: refactor

    def _extract_meal_name(self, meal_info: str) -> str | None:
        """Extract meal name from meal info string."""
        if "(ID:" in meal_info:
            return meal_info.split("(ID:")[0].strip()
        return meal_info

    async def _get_ingredients_for_meals(
        self, user_id: int, meal_names: list[str]
    ) -> set[str]:
        """Get ingredients for specified meals."""
        ingredients: set[str] = set()
        # FIXME: refactor
        recipes = await asyncio.gather(
            *(
                self.recipe_manager.get_recipe_by_name(user_id, meal_name)
                for meal_name in meal_names
            ),
            return_exceptions=True
        )
    
        for recipe in recipes:
            if isinstance(recipe, Exception):
                logging.error(f"Error fetching recipe: {recipe}")
                continue
            
            if recipe and recipe.ingredients:
                ingredients.update(recipe.ingredients)
            
        return ingredients
    # FIXME: refactor
