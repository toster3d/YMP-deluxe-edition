from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any

class AbstractUserPlanManager(ABC):
    @abstractmethod
    def add_plan(self, user_id: int, date: datetime) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def update_meal(self, user_id: int, date: datetime, meal_name: str, meal_value: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_plans(self, user_id: int, date: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def create_or_update_plan(self, user_id: int, selected_date: datetime, user_plan: str, meal_name: str) -> None:
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
        self.db.execute(
            "INSERT INTO userPlan (user_id, date) VALUES (?, ?)",
            user_id,
            date.strftime("%Y-%m-%d")
        )
            
    def update_meal(self, user_id: int, date: datetime, meal_name: str, meal_value: str) -> None:
        if not meal_name:
            raise ValueError("meal_name cannot be empty")
        self.db.execute(
            f"UPDATE userPlan SET {meal_name} = ? WHERE user_id = ? AND date = ?",
            meal_value,
            user_id,
            date.strftime("%Y-%m-%d")
        )

    def get_plans(self, user_id: int, date: datetime) -> list[dict[str, Any]]:
        plans: Any = self.db.execute(
            "SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = ? AND date = ?",
            user_id,
            date.strftime("%Y-%m-%d")
        )
        return plans if plans else []

    def create_or_update_plan(self, user_id: int, selected_date: datetime, user_plan: str, meal_name: str) -> None:
        existing_plan: list[dict[str, Any]] = self.get_plans(user_id, selected_date)
        if not existing_plan:
            self.add_plan(user_id, selected_date)
        self.update_meal(user_id, selected_date, user_plan, meal_name)

    def get_user_meals(self, user_id: int, date: datetime) -> list[dict[str, Any]]:
        return self.db.execute(
            "SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = ? AND date = ?",
            user_id,
            date.strftime("%Y-%m-%d")
        )

    def get_user_recipes(self, user_id: int) -> list[dict[str, Any]]:
        return self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = ?",
            user_id
        )