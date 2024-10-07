from abc import ABC, abstractmethod
from flask import current_app
from typing import Any

class AbstractRecipeManager(ABC):
    @abstractmethod
    def get_recipes_list(self, user_id: int)-> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipes(self, user_id: int)-> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int, user_id: int)-> list[dict[str, Any]] | None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipe_by_name(self, user_id: int, meal_name: str)-> list[dict[str, Any]] | None:
        raise NotImplementedError('message')

    @abstractmethod
    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str)-> None:
        raise NotImplementedError('message')

    @abstractmethod
    def update_recipe(self, recipe_id: int, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipes_ordered_by_meal_type(self, user_id: int)-> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_ingredients_by_meal_name(self, user_id: int, meal: str)-> list[dict[str, Any]] | None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_meal_names(self, user_id: int)-> list[dict[str, Any]]:
        raise NotImplementedError('message')

class RecipeManager(AbstractRecipeManager):
    def __init__(self, db: Any) -> None:
        self.db = db

    def get_recipes_list(self, user_id: int):
        return self.db.execute(
            "SELECT id, mealName, mealType FROM Recipes1 WHERE user_id = :user_id "
            "ORDER BY mealName COLLATE NOCASE ASC",
            user_id=user_id
        )

    def get_recipes(self, user_id: int):
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id",
            user_id=user_id
        )

    def get_recipe_by_id(self, recipe_id: int, user_id: int):
        recipe: Any = self.db.execute(
            "SELECT * FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id
        )
        return recipe[0] if recipe else None

    def get_recipe_by_name(self, user_id: int, meal_name: str):
        recipe: Any = self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id AND mealName = :meal_name",
            user_id=user_id,
            meal_name=meal_name
        )
        return recipe[0] if recipe else None

    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        try:
            self.db.execute(
                "INSERT INTO Recipes1(user_id, mealName, mealType, ingredients, instructions) "
                "VALUES(:user_id, :mealName, :mealType, :ingredients, :instructions)",
                user_id=user_id,
                mealName=meal_name,
                mealType=meal_type,
                ingredients=ingredients,
                instructions=instructions
            )
        except Exception as e:
            current_app.logger.error(f"Error adding recipe: {str(e)}")
            raise RuntimeError("Failed to add recipe") from e

    def update_recipe(self, recipe_id: int, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        self.db.execute(
            "UPDATE Recipes1 SET mealName = :mealName, mealType = :mealType, "
            "ingredients = :ingredients, instructions = :instructions "
            "WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id,
            mealName=meal_name,
            mealType=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )

    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        self.db.execute(
            "DELETE FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id
        )
        current_app.logger.info("Your recipe was successfully deleted!")

    def get_recipes_ordered_by_meal_type(self, user_id: int):
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id ORDER BY mealType",
            user_id=user_id
        )

    def get_ingredients_by_meal_name(self, user_id: int, meal: str)-> list[dict[str, Any]] | None:
        recipe = self.db.execute(
            "SELECT ingredients FROM Recipes1 WHERE user_id = :user_id AND mealName = :meal_name",
            user_id=user_id,
            meal_name=meal
        )
        return recipe[0]['ingredients'] if recipe else None

    def get_meal_names(self, user_id: int) -> list[Any]:
        meals = self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = :user_id",
            user_id=user_id
        )
        return [meal['mealName'] for meal in meals]
