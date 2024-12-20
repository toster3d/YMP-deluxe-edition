from datetime import date as date_type
from typing import Any, TypedDict

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from extensions import get_async_db
from services.user_plan_manager import SqliteUserPlanManager

from .pydantic_schemas import PlanSchema


class UserPlansDict(TypedDict):
    user_id: int
    breakfast: str | None
    lunch: str | None
    dinner: str | None
    dessert: str | None


class ScheduleResponse(TypedDict):
    date: str
    user_plans: UserPlansDict


class ScheduleResource:
    """Resource for handling user schedules."""
    
    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize resource with database session."""
        self.user_plan_manager = SqliteUserPlanManager(db)
        self.db = db

    async def get(self, user_id: int, date_param: date_type | None = None) -> ScheduleResponse:
        """Get user's schedule for a specific date."""
        try:
            selected_date: date_type = date_param or date_type.today()
            user_plans = await self.user_plan_manager.get_plans(user_id, selected_date)
            
            return {
                "date": selected_date.isoformat(),
                "user_plans": {
                    "user_id": user_id,
                    "breakfast": user_plans.get("breakfast"),
                    "lunch": user_plans.get("lunch"),
                    "dinner": user_plans.get("dinner"),
                    "dessert": user_plans.get("dessert"),
                }
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {str(e)}"
            )


class ChooseMealResource:
    """Resource for handling meal choices."""
    
    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize resource with database session."""
        self.user_plan_manager = SqliteUserPlanManager(db)

    async def get(self, user_id: int) -> dict[str, list[dict[str, Any]]]:
        """
        Get available recipes for user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: List of available recipes
        """
        recipes = await self.user_plan_manager.get_user_recipes(user_id)
        return {'recipes': recipes}

    async def post(self, user_id: int, plan_data: PlanSchema) -> dict[str, Any]:
        """Create or update meal plan."""
        try:
            updated_plan = await self.user_plan_manager.create_or_update_plan(
                user_id=user_id,
                selected_date=plan_data.selected_date,
                recipe_id=plan_data.recipe_id,
                meal_type=plan_data.meal_type
            )
            
            return {
                "message": "Meal plan updated successfully!",
                **updated_plan
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while updating the meal plan: {str(e)}"
            )
