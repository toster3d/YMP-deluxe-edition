import json
from abc import ABC, abstractmethod
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import Recipe


class RecipeDict(TypedDict):
    id: int
    meal_name: str
    meal_type: str
    ingredients: list[str]
    instructions: list[str]

class AbstractRecipeManager(ABC):
    @abstractmethod
    async def get_recipes(self, user_id: int) -> list[RecipeDict]:
        """Retrieve a list of recipes for the specified user ID."""
        pass

    @abstractmethod
    async def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeDict | None:
        """Fetch a recipe by its ID for the specified user ID."""
        pass

    @abstractmethod
    async def add_recipe(
        self, 
        user_id: int, 
        meal_name: str, 
        meal_type: str, 
        ingredients: list[str], 
        instructions: list[str]
    ) -> Recipe:
        """Add a new recipe for the specified user ID."""
        pass

    @abstractmethod
    async def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        meal_name: str | None = None,
        meal_type: str | None = None,
        ingredients: list[str] | None = None,
        instructions: list[str] | None = None
    ) -> Recipe | None:
        """Update an existing recipe for the specified user ID."""
        pass

    @abstractmethod
    async def delete_recipe(self, recipe_id: int, user_id: int) -> bool:
        """Delete a recipe for the specified user ID."""
        pass

    @abstractmethod
    async def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> str | None:
        """Retrieve ingredients for a recipe by its meal name for the specified user ID."""
        pass

class RecipeManager(AbstractRecipeManager):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recipes(self, user_id: int) -> list[RecipeDict]:
        query = select(Recipe).filter_by(user_id=user_id)
        result = await self.db.execute(query)
        recipes = result.scalars().all()
        
        return [
            RecipeDict(
                id=recipe.id,
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions)
            )
            for recipe in recipes
        ]

    async def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeDict | None:
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if recipe:
            return RecipeDict(
                id=recipe.id,
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions)
            )
        return None

    async def add_recipe(
        self, 
        user_id: int, 
        meal_name: str, 
        meal_type: str, 
        ingredients: list[str], 
        instructions: list[str]
    ) -> Recipe:
        new_recipe = Recipe(
            user_id=user_id,
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=json.dumps(ingredients),
            instructions=json.dumps(instructions)
        )
        self.db.add(new_recipe)
        await self.db.commit()
        await self.db.refresh(new_recipe)
        return new_recipe

    async def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        meal_name: str | None = None,
        meal_type: str | None = None,
        ingredients: list[str] | None = None,
        instructions: list[str] | None = None
    ) -> Recipe | None:
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if recipe:
            if meal_name is not None:
                recipe.meal_name = meal_name
            if meal_type is not None:
                recipe.meal_type = meal_type
            if ingredients is not None:
                recipe.ingredients = json.dumps(ingredients)
            if instructions is not None:
                recipe.instructions = json.dumps(instructions)
                
            await self.db.commit()
            await self.db.refresh(recipe)
            return recipe
        return None

    async def delete_recipe(self, recipe_id: int, user_id: int) -> bool:
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if recipe:
            await self.db.delete(recipe)
            await self.db.commit()
            return True
        return False

    async def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> str | None:
        query = select(Recipe).filter_by(user_id=user_id, meal_name=meal)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        return recipe.ingredients if recipe else None
