import logging
from datetime import date

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from extensions import get_async_db
from services.recipe_manager import RecipeManager
from services.shopping_list_service import ShoppingListService
from services.user_plan_manager import SqlAlchemyUserPlanManager

from .pydantic_schemas import (
    DateRangeSchema,
    ShoppingListRangeResponse,
    ShoppingListResponse,
)

logger = logging.getLogger(__name__)

class ShoppingListResource:
    """Resource for handling shopping lists."""

    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize shopping list resource with database session."""
        self.recipe_manager = RecipeManager(db)
        self.user_plan_manager = SqlAlchemyUserPlanManager(db)
        self.shopping_list_service = ShoppingListService(
            self.user_plan_manager, self.recipe_manager
        )

    async def get(self, user_id: int) -> ShoppingListResponse:
        """Get shopping list for today."""
        logger.info(f"Fetching shopping list for user {user_id} for today")
        today: date = date.today()
        try:
            ingredients = await self.shopping_list_service.get_ingredients_for_date_range(
                user_id, (today, today)
            )
            if not ingredients:
                logger.warning(f"No meal plan found for user {user_id} today")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No meal plan for today. Check your schedule.",
                )
            
            return ShoppingListResponse(
                ingredients=list(ingredients),
                current_date=today.isoformat()
            )
        except Exception:
            logger.exception("Error fetching shopping list")
            raise

    async def post(
        self, user_id: int, date_range_data: DateRangeSchema
    ) -> ShoppingListRangeResponse:
        """
        Get shopping list for date range.

        Args:
            user_id: ID of the user
            date_range_data: Start and end dates

        Returns:
            dict: Shopping list with ingredients

        Raises:
            HTTPException: If no meal plan found
        """
        ingredients = await self.shopping_list_service.get_ingredients_for_date_range(
            user_id, (date_range_data.start_date, date_range_data.end_date)
        )

        if not ingredients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No meal plan for this date range.",
            )

        return ShoppingListRangeResponse(
            ingredients=list(ingredients),
            date_range=f"{date_range_data.start_date.isoformat()} to {date_range_data.end_date.isoformat()}"
        )
