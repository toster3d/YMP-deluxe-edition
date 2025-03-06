import asyncio
import logging
from datetime import date
from typing import Any, Generator

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
        self.logger = logging.getLogger(__name__)

    async def get_ingredients_for_date_range(
        self, user_id: int, date_range: tuple[date, date]
    ) -> set[str]:
        """
        Get ingredients for meal plans in date range.
        
        Args:
            user_id: User identifier
            date_range: Tuple containing start and end dates
            
        Returns:
            Set of ingredient names
        """
        start_date, end_date = date_range
        ingredients: set[str] = set()
        date_list = generate_date_list(start_date, end_date)
        
        self.logger.info(
            f"Fetching ingredients for user {user_id} from {start_date} to {end_date}"
        )
                
        all_meal_names: list[str] = []
        for current_date in date_list:
            user_plan: dict[str, Any] | None = await self.user_plan_manager.get_plans(user_id=user_id, date=current_date)
            
            if user_plan:
                meal_names: Generator[str, None, None] = self._get_meal_names(user_plan)
                if meal_names:
                    all_meal_names.extend(meal_names)
                    self.logger.debug(
                        f"Found meals for {current_date}: {', '.join(meal_names)}"
                    )
        
        if not all_meal_names:
            self.logger.warning(
                f"No meal plans found for user {user_id} in date range {start_date} to {end_date}"
            )
            return ingredients
            
        unique_meal_names = list(set(all_meal_names))
        self.logger.info(f"Found {len(unique_meal_names)} unique meals to process")
        
        tasks = [
            self._safe_get_ingredients(user_id, meal_name)
            for meal_name in unique_meal_names
        ]
        
        all_ingredients = await asyncio.gather(*tasks)
        
        for ingredient_list in all_ingredients:
            if ingredient_list:
                ingredients.update(ingredient_list)
                
        self.logger.info(f"Generated shopping list with {len(ingredients)} ingredients")
        return ingredients
    
    async def _safe_get_ingredients(self, user_id: int, meal_name: str) -> list[str]:
        """
        Safely get ingredients for a meal, handling exceptions.
        
        Args:
            user_id: User identifier
            meal_name: Name of the meal
            
        Returns:
            List of ingredients or empty list on error
        """
        try:
            ingredients = await self.recipe_manager.get_ingredients_by_meal_name(user_id, meal_name)
            if not ingredients:
                self.logger.debug(f"No ingredients found for meal '{meal_name}'")
                return []
                
            self.logger.debug(f"Found {len(ingredients)} ingredients for meal '{meal_name}'")
            return ingredients
        except Exception as e:
            self.logger.warning(f"Error fetching ingredients for '{meal_name}': {e}")
            return []
    
    def _get_meal_names(self, user_plan: dict[str, Any]) -> Generator[str, None, None]:
        """
        Extract meal names from user plan.
        
        Args:
            user_plan: Dictionary containing meal plan details
            
        Returns:
            List of meal names
        """
        for meal_type in ["breakfast", "lunch", "dinner", "dessert"]:
            meal_info: Any | None = user_plan.get(meal_type)
            if meal_info:
                meal_name: str | None = self._extract_meal_name(str(meal_info))
                if meal_name:
                    yield meal_name

    def _extract_meal_name(self, meal_info: str) -> str | None:
        """
        Extract meal name from meal info string.
        
        Args:
            meal_info: String containing meal information
            
        Returns:
            Extracted meal name or None if not found
        """
        if not meal_info or meal_info.lower() in ('none', 'null', ''):
            return None
            
        if "(ID:" in meal_info:
            return meal_info.split("(ID:")[0].strip()
        
        if " - " in meal_info:
            return meal_info.split(" - ")[0].strip()
            
        return meal_info.strip()