from datetime import datetime
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

    async def get(self, user_id: int, date_str: str | None = None) -> ScheduleResponse:
        """
        Get user schedule for a specific date.
        
        Args:
            user_id: ID of the user
            date_str: Optional date string in format "Day DD Month YYYY"
            
        Returns:
            ScheduleResponse: User's schedule for the specified date
            
        Raises:
            HTTPException: If date format is invalid
        """
        try:
            if date_str is None:
                date_str = datetime.now().strftime("%A %d %B %Y")
                
            selected_date = datetime.strptime(date_str, "%A %d %B %Y").date()
            user_plans = await self.user_plan_manager.get_plans(user_id, selected_date)

            return {
                "date": date_str,
                "user_plans": {
                    "user_id": user_id,
                    "breakfast": user_plans.get("breakfast"),
                    "lunch": user_plans.get("lunch"),
                    "dinner": user_plans.get("dinner"),
                    "dessert": user_plans.get("dessert"),
                }
            }
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format"
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
        """
        Create or update meal plan.
        
        Args:
            user_id: ID of the user
            plan_data: Plan data from request
            
        Returns:
            dict: Updated plan details
            
        Raises:
            HTTPException: If plan creation/update fails
        """
        try:
            selected_date_obj = datetime.strptime(
                plan_data.selected_date.strftime("%A %d %B %Y"), 
                "%A %d %B %Y"
            )
            
            updated_plan = await self.user_plan_manager.create_or_update_plan(
                user_id=user_id,
                selected_date=selected_date_obj,
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
