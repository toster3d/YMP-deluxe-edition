from datetime import date as date_type
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any
from models.recipes import UserPlan, Recipe
from flask import current_app
from flask_sqlalchemy import SQLAlchemy


class AbstractUserPlanManager(ABC):
    @abstractmethod
    def get_plans(self, user_id: int, date: date_type) -> dict[str, int | date_type | str]:
        raise NotImplementedError('This method should retrieve the meal plans for a user on a specific date.')

    @abstractmethod
    def create_or_update_plan(self, user_id: int, selected_date: datetime, recipe_id: int, meal_type: str) -> dict[str, Any]:
        raise NotImplementedError('This method should create or update a meal plan for the user on the specified date with the given recipe ID and meal type.')

    @abstractmethod
    def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError('This method should retrieve a list of recipes associated with the specified user ID.')


class SqliteUserPlanManager(AbstractUserPlanManager):
    def __init__(self, db: SQLAlchemy) -> None:
        self.db: SQLAlchemy = db

    def get_plans(self, user_id: int, date: date_type) -> dict[str, int | date_type | str]:
        current_app.logger.info(f"Attempting to get plan for user_id: {user_id}, date: {date}")

      
        date_only = date 
        current_app.logger.info(f"Using date for query: {date_only}")

        plan: UserPlan | None = self.db.session.query(UserPlan).filter(
            UserPlan.user_id == user_id,
            UserPlan.date == date_only
        ).first()

        if plan:
            result: dict[str, int | date_type | str] = {
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
            current_app.logger.info(f"No plan found for date: {date_only}")

        return result

    def create_or_update_plan(self, user_id: int, selected_date: datetime, recipe_id: int, meal_type: str) -> dict[str, Any]:
        current_app.logger.info(f"Creating or updating plan for user_id: {user_id}, date: {selected_date}, recipe_id: {recipe_id}, meal_type: {meal_type}")
        
        selected_date_only = selected_date.date()
        
        plan: UserPlan | None = self.db.session.query(UserPlan).filter_by(user_id=user_id, date=selected_date_only).first()
        
        if plan is None: 
            plan = UserPlan(user_id=user_id, date=selected_date_only)
            self.db.session.add(plan)

        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(id=recipe_id).first()
        if not recipe:
            raise ValueError(f"Recipe with id {recipe_id} not found")

        meal_info: str = recipe.meal_name

        if meal_type in ['breakfast', 'lunch', 'dinner', 'dessert']:
            setattr(plan, meal_type, meal_info)
        else:
            current_app.logger.error(f"Invalid meal_type: {meal_type}")
            raise ValueError(f"Invalid meal_type: {meal_type}")

        self.db.session.commit()
        current_app.logger.info(f"Plan updated: {plan}")

        return {
            "meal_type": meal_type,
            "recipe_name": recipe.meal_name,
            "recipe_id": recipe_id,
            "date": selected_date_only
        }

    def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        recipes: list[Recipe] = self.db.session.query(Recipe).filter_by(user_id=user_id).all()
        return [
            {
                'id': recipe.id,
                'name': recipe.meal_name,
                'meal_type': recipe.meal_type,
            }
            for recipe in recipes
        ]
