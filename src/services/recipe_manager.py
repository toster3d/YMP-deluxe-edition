from abc import ABC, abstractmethod
from typing import Any, Optional
from src.models.recipes import Recipe

class AbstractRecipeManager(ABC):
    @abstractmethod
    def get_recipes_list(self, user_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipes(self, user_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> Optional[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipe_by_name(self, user_id: int, meal_name: str) -> Optional[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def update_recipe(self, recipe_id: int, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        raise NotImplementedError('message')

    @abstractmethod
    def get_recipes_ordered_by_meal_type(self, user_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> Optional[str]:
        raise NotImplementedError('message')

    @abstractmethod
    def get_meal_names(self, user_id: int) -> list[str]:
        raise NotImplementedError('message')

class RecipeManager(AbstractRecipeManager):
    def __init__(self, db: Any) -> None:
        self.db = db

    def get_recipes_list(self, user_id: int) -> list[dict[str, Any]]:
        recipes = Recipe.query.filter_by(user_id=user_id).order_by(Recipe.meal_name.asc()).all()
        return [{'id': recipe.id, 'meal_name': recipe.meal_name, 'meal_type': recipe.meal_type} for recipe in recipes]

    def get_recipes(self, user_id: int) -> list[dict[str, Any]]:
        recipes = self.db.session.query(Recipe).filter_by(user_id=user_id).all()
        return [
            {
                'id': recipe.id,
                'meal_name': recipe.meal_name,
                'meal_type': recipe.meal_type,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions
            }
            for recipe in recipes
        ]

    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> Optional[dict[str, Any]]:
        recipe = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            return {
                'id': recipe.id,
                'meal_name': recipe.meal_name,
                'meal_type': recipe.meal_type,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions
            }
        return None

    def get_recipe_by_name(self, user_id: int, meal_name: str) -> Optional[dict[str, Any]]:
        recipe = Recipe.query.filter_by(user_id=user_id, meal_name=meal_name).first()
        if recipe:
            return {
                'id': recipe.id,
                'meal_name': recipe.meal_name,
                'meal_type': recipe.meal_type,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions
            }
        return None

    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        new_recipe = Recipe(
            user_id=user_id,
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )
        self.db.session.add(new_recipe)
        self.db.session.commit()

    def update_recipe(self, recipe_id: int, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        recipe = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            recipe.meal_name = meal_name
            recipe.meal_type = meal_type
            recipe.ingredients = ingredients
            recipe.instructions = instructions
            self.db.session.commit()
        else:
            raise ValueError("Recipe not found")

    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        recipe = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            self.db.session.delete(recipe)
            self.db.session.commit()
        else:
            raise ValueError("Recipe not found")

    def get_recipes_ordered_by_meal_type(self, user_id: int) -> list[dict[str, Any]]:
        recipes = Recipe.query.filter_by(user_id=user_id).order_by(Recipe.meal_type).all()
        return [{'id': recipe.id, 'meal_name': recipe.meal_name, 'meal_type': recipe.meal_type} for recipe in recipes]

    def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> Optional[str]:
        recipe = Recipe.query.filter_by(user_id=user_id, meal_name=meal).first()
        return recipe.ingredients if recipe else None

    def get_meal_names(self, user_id: int) -> list[str]:
        meals = Recipe.query.filter_by(user_id=user_id).all()
        return [recipe.meal_name for recipe in meals]