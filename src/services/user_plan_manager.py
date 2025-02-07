from abc import ABC, abstractmethod
from datetime import date as date_type
from typing import Any

from sqlalchemy import select

from extensions import DbSession
from models.recipes import Recipe, UserPlan


class AbstractUserPlanManager(ABC):
    @abstractmethod
    async def get_plans(self, user_id: int, date: date_type) -> dict[str, Any]:
        """Retrieve user plans for a specific date."""
        raise NotImplementedError()

    @abstractmethod
    async def create_or_update_plan(
        self, user_id: int, selected_date: date_type, recipe_id: int, meal_type: str
    ) -> dict[str, Any]:
        """Create or update a meal plan for the user."""
        raise NotImplementedError()

    @abstractmethod
    async def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        """Retrieve a list of recipes for the specified user ID."""
        raise NotImplementedError()


class SqlAlchemyUserPlanManager(AbstractUserPlanManager):
    def __init__(self, db: DbSession) -> None:
        """Initialize the user plan manager with a database session."""
        self.db = db

    async def get_plans(self, user_id: int, date: date_type) -> dict[str, Any]:
        """Get user plans for specific date."""
        query = select(UserPlan).filter(
            UserPlan.user_id == user_id, 
            UserPlan.date == date
        )
        result = await self.db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            return {
                "user_id": user_id,
                "date": date,
                "breakfast": None,
                "lunch": None,
                "dinner": None,
                "dessert": None,
            }

        return {
            "user_id": plan.user_id,
            "date": plan.date,
            "breakfast": plan.breakfast,
            "lunch": plan.lunch,
            "dinner": plan.dinner,
            "dessert": plan.dessert,
        }

    async def create_or_update_plan(
        self, user_id: int, selected_date: date_type, recipe_id: int, meal_type: str
    ) -> dict[str, Any]:
        """Create or update a meal plan for the user."""
        async with self.db.begin():
            plan = await self.db.execute(
                select(UserPlan).filter_by(user_id=user_id, date=selected_date)
            )
            plan_instance = plan.scalar_one_or_none()

            if plan_instance is None:
                plan_instance = UserPlan(user_id=user_id, date=selected_date)
                self.db.add(plan_instance)

            recipe = await self.db.execute(select(Recipe).filter_by(id=recipe_id))
            recipe_instance = recipe.scalar_one_or_none()
            if not recipe_instance:
                raise ValueError(f"Recipe with id {recipe_id} not found")

            if meal_type in ["breakfast", "lunch", "dinner", "dessert"]:
                setattr(plan_instance, meal_type, recipe_instance.meal_name)
            else:
                raise ValueError(f"Invalid meal_type: {meal_type}")

            await self.db.commit()
            return {
                "meal_type": meal_type,
                "recipe_name": recipe_instance.meal_name,
                "recipe_id": recipe_id,
                "date": selected_date.isoformat(),
            }

    async def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        """Retrieve a list of recipes for the specified user ID."""
        recipes = await self.db.execute(select(Recipe).filter_by(user_id=user_id))
        return [
            {
                "id": recipe.id,
                "name": recipe.meal_name,
                "meal_type": recipe.meal_type,
            }
            for recipe in recipes.scalars()
        ]
