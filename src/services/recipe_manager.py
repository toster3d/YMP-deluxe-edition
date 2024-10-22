from abc import ABC, abstractmethod
from typing import TypedDict
from models.recipes import Recipe
from flask_sqlalchemy import SQLAlchemy


class RecipeDict(TypedDict):
    id: int
    meal_name: str
    meal_type: str
    ingredients: str
    instructions: str
    
    
class AbstractRecipeManager(ABC):

    @abstractmethod
    def get_recipes(self, user_id: int) -> list[RecipeDict] | None:
        raise NotImplementedError('Retrieve a list of recipes for the specified user ID.')

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeDict | None:
        raise NotImplementedError('Fetch a recipe by its ID for the specified user ID.')

    @abstractmethod
    def get_recipe_by_name(self, user_id: int, meal_name: str) -> RecipeDict | None:
        raise NotImplementedError('Find a recipe by its name for the specified user ID.')

    @abstractmethod
    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        raise NotImplementedError('Add a new recipe for the specified user ID with the provided details.')

    @abstractmethod
    def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        meal_name: str | None = None,
        meal_type: str | None = None,
        ingredients: str | None = None,
        instructions: str | None = None
    ) -> None:
        raise NotImplementedError('Update an existing recipe for the specified user ID.')

    @abstractmethod
    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        raise NotImplementedError('Delete a recipe by its ID for the specified user ID.')

    @abstractmethod
    def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> str | None:
        raise NotImplementedError('Retrieve ingredients for a recipe by its meal name for the specified user ID.')



class RecipeManager(AbstractRecipeManager):
    def __init__(self, db: SQLAlchemy) -> None:
        self.db: SQLAlchemy = db

    def get_recipes(self, user_id: int) -> list[RecipeDict]:
        recipes: list[Recipe] = self.db.session.query(Recipe).filter_by(user_id=user_id).all()
        return [
            RecipeDict(
                id=recipe.id,
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions
            )
            for recipe in recipes
        ]

    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeDict | None:
        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            return RecipeDict(
                id=recipe.id,
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions
            )

    def get_recipe_by_name(self, user_id: int, meal_name: str) -> RecipeDict | None:
        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(user_id=user_id, meal_name=meal_name).first()
        if recipe:
            return RecipeDict(
                id=recipe.id,
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions
            )

    def add_recipe(self, user_id: int, meal_name: str, meal_type: str, ingredients: str, instructions: str) -> None:
        new_recipe: Recipe = Recipe(
            user_id=user_id,
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )
        self.db.session.add(new_recipe)
        self.db.session.commit()

    def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        meal_name: str | None = None,
        meal_type: str | None = None,
        ingredients: str | None = None,
        instructions: str | None = None
    ) -> None:
        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            if meal_name is not None:
                recipe.meal_name = meal_name
            if meal_type is not None:
                recipe.meal_type = meal_type
            if ingredients is not None:
                recipe.ingredients = ingredients
            if instructions is not None:
                recipe.instructions = instructions
            self.db.session.commit()
        else:
            raise ValueError("Recipe not found")

    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(id=recipe_id, user_id=user_id).first()
        if recipe:
            self.db.session.delete(recipe)
            self.db.session.commit()
        else:
            raise ValueError("Recipe not found")

    def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> str | None:
        recipe: Recipe | None = self.db.session.query(Recipe).filter_by(user_id=user_id, meal_name=meal).first()
        return recipe.ingredients if recipe else None
