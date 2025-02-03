import json

from sqlalchemy import select

from extensions import DbSession
from models.recipes import Recipe
from resources.pydantic_schemas import RecipeUpdateSchema


class RecipeManager:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    async def get_recipes(self, user_id: int) -> list[RecipeUpdateSchema]:
        query = select(Recipe).filter_by(user_id=user_id)
        result = await self.db.execute(query)
        recipes = result.scalars().all()

        return [
            RecipeUpdateSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
            for recipe in recipes
        ]

    async def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeUpdateSchema | None:
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        if recipe is not None:
            return RecipeUpdateSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
        return None

    async def get_recipe_by_name(
        self, user_id: int, meal_name: str
    ) -> RecipeUpdateSchema | None:
        """Find a recipe by its name for the specified user ID."""
        query = select(Recipe).filter_by(user_id=user_id, meal_name=meal_name)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()

        if recipe:
            return RecipeUpdateSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
        return None

    async def add_recipe(
        self,
        user_id: int,
        meal_name: str,
        meal_type: str,
        ingredients: list[str],
        instructions: list[str],
    ) -> Recipe:
        new_recipe = Recipe(
            user_id=user_id,
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=json.dumps(ingredients),
            instructions=json.dumps(instructions),
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
        instructions: list[str] | None = None,
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
