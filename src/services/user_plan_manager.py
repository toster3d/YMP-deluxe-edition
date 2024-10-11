from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from abc import ABC, abstractmethod
from typing import Any, Optional
from src.models.recipes import UserPlan, Recipe
from flask import current_app


class AbstractUserPlanManager(ABC):
    @abstractmethod
    def add_plan(self, user_id: int, date: datetime) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def update_meal(self, user_id: int, date: datetime, meal_name: str, meal_value: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_plans(self, user_id: int, date: datetime) -> Optional[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def create_or_update_plan(self, user_id: int, selected_date: datetime, recipe_id: int, meal_type: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_user_meals(self, user_id: int, date: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError('message')


class SqliteUserPlanManager(AbstractUserPlanManager):
    def __init__(self, db: Any) -> None:
        self.db: Any = db

    def add_plan(self, user_id: int, date: datetime) -> None:
        new_plan = UserPlan(
            user_id=user_id,
            date=date,
            breakfast=None,
            lunch=None,
            dinner=None,
            dessert=None
        )
        self.db.session.add(new_plan)
        self.db.session.commit()

    def update_meal(self, user_id: int, date: datetime, meal_name: str, meal_value: str) -> None:
        if not meal_name:
            raise ValueError("meal_name cannot be empty")
        plan = self.db.session.query(UserPlan).filter_by(user_id=user_id, date=date).first()
        if plan:
            setattr(plan, meal_name, meal_value)
            self.db.session.commit()

    def get_plans(self, user_id: int, date: datetime | date) -> Optional[dict[str, Any]]:
        if isinstance(date, datetime):
            date = date.date()

        current_app.logger.info(f"Attempting to get plan for user_id: {user_id}, date: {date}")

        plan = self.db.session.query(UserPlan).filter(
            UserPlan.user_id == user_id,
            func.date(UserPlan.date) == date
        ).first()

        if plan:
            result = {
                'user_id': plan.user_id,
                'date': plan.date,
                'breakfast': plan.breakfast,
                'lunch': plan.lunch,
                'dinner': plan.dinner,
                'dessert': plan.dessert
            }
            current_app.logger.info(f"Found plan: {result}")
        else:
            result = {}
            current_app.logger.info(f"No plan found for date: {date}")

        return result

    def create_or_update_plan(self, user_id: int, selected_date: datetime, recipe_id: int, meal_type: str) -> None:
        current_app.logger.info(f"Creating or updating plan for user_id: {user_id}, date: {selected_date}, recipe_id: {recipe_id}, meal_type: {meal_type}")

        try:
            plan = self.db.session.query(UserPlan).filter_by(user_id=user_id, date=selected_date).one()
        except NoResultFound:
            plan = UserPlan(user_id=user_id, date=selected_date)
            self.db.session.add(plan)

        recipe = self.db.session.query(Recipe).filter_by(id=recipe_id).first()
        if not recipe:
            raise ValueError(f"Recipe with id {recipe_id} not found")

        meal_info = f"{recipe.meal_name} (ID: {recipe_id})"

        if meal_type in ['breakfast', 'lunch', 'dinner', 'dessert']:
            setattr(plan, meal_type, meal_info)
        else:
            current_app.logger.error(f"Invalid meal_type: {meal_type}")
            raise ValueError(f"Invalid meal_type: {meal_type}")

        self.db.session.commit()
        current_app.logger.info(f"Plan updated: {plan}")

    def get_user_meals(self, user_id: int, date: datetime) -> list[dict[str, Any]]:
        return self.get_plans(user_id, date)

    def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        recipes = self.db.session.query(Recipe).filter_by(user_id=user_id).all()
        return [
            {
                'id': recipe.id,
                'name': recipe.meal_name,
                'meal_type': recipe.meal_type,
            }
            for recipe in recipes
        ]

