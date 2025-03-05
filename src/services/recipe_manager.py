import json
from abc import ABC, abstractmethod

from sqlalchemy import select

from extensions import DbSession
from models.recipes import Recipe
from resources.pydantic_schemas import RecipeSchema, RecipeUpdateSchema


class AbstractRecipeManager(ABC):
    @abstractmethod
    async def get_recipes(self, user_id: int) -> list[RecipeSchema]:
        raise NotImplementedError(
            "Retrieve a list of recipes for the specified user ID."
        )

    @abstractmethod
    async def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeUpdateSchema | None:
        """Fetch a recipe by its ID for update operations."""
        raise NotImplementedError()

    @abstractmethod
    async def get_recipe_details(self, recipe_id: int, user_id: int) -> RecipeSchema | None:
        """Fetch complete recipe details by its ID."""
        raise NotImplementedError()

    @abstractmethod
    async def get_recipe_by_name(
        self, user_id: int, meal_name: str
    ) -> RecipeSchema | None:
        raise NotImplementedError(
            "Find a recipe by its name for the specified user ID."
        )

    @abstractmethod
    async def add_recipe(
        self,
        user_id: int,
        recipe_data: RecipeSchema,
    ) -> Recipe:
        raise NotImplementedError(
            "Add a new recipe for the specified user ID with the provided details."
        )

    @abstractmethod
    async def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        recipe_data: RecipeUpdateSchema,
    ) -> Recipe | None:
        raise NotImplementedError(
            "Update an existing recipe for the specified user ID."
        )

    @abstractmethod
    async def delete_recipe(self, recipe_id: int, user_id: int) -> bool:
        raise NotImplementedError(
            "Delete a recipe by its ID for the specified user ID."
        )

    @abstractmethod
    async def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> list[str] | None:
        raise NotImplementedError(
            "Retrieve ingredients for a recipe by its meal name for the specified user ID."
        )


class RecipeManager(AbstractRecipeManager):
    def __init__(self, db: DbSession) -> None:
        self.db = db

    async def get_recipes(self, user_id: int) -> list[RecipeSchema]:
        query = select(Recipe).filter_by(user_id=user_id)
        result = await self.db.execute(query)
        recipes = result.scalars().all()

        return [
            RecipeSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
            for recipe in recipes
        ]

    async def get_recipe_by_id(self, recipe_id: int, user_id: int) -> RecipeUpdateSchema | None:
        """Fetch a recipe for update operations."""
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

    async def get_recipe_details(self, recipe_id: int, user_id: int) -> RecipeSchema | None:
        """Fetch complete recipe details."""
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if recipe is not None:
            return RecipeSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
        return None

    async def get_recipe_by_name(
        self, user_id: int, meal_name: str
    ) -> RecipeSchema | None:
        """Find a recipe by its name for the specified user ID."""
        query = select(Recipe).filter_by(user_id=user_id, meal_name=meal_name)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()

        if recipe:
            return RecipeSchema(
                meal_name=recipe.meal_name,
                meal_type=recipe.meal_type,
                ingredients=json.loads(recipe.ingredients),
                instructions=json.loads(recipe.instructions),
            )
        return None

    async def add_recipe(
        self,
        user_id: int,
        recipe_data: RecipeSchema,
    ) -> Recipe:
        new_recipe = Recipe(
            user_id=user_id,
            meal_name=recipe_data.meal_name,
            meal_type=recipe_data.meal_type,
            ingredients=json.dumps(recipe_data.ingredients),
            instructions=json.dumps(recipe_data.instructions),
        )
        self.db.add(new_recipe)
        await self.db.commit()
        await self.db.refresh(new_recipe)
        return new_recipe

    async def update_recipe(
        self,
        recipe_id: int,
        user_id: int,
        recipe_data: RecipeUpdateSchema,
    ) -> Recipe | None:
        query = select(Recipe).filter_by(id=recipe_id, user_id=user_id)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()

        if recipe:
            if recipe_data.meal_name is not None:
                recipe.meal_name = recipe_data.meal_name
            if recipe_data.meal_type is not None:
                recipe.meal_type = recipe_data.meal_type
            if recipe_data.ingredients is not None:
                recipe.ingredients = json.dumps(recipe_data.ingredients)
            if recipe_data.instructions is not None:
                recipe.instructions = json.dumps(recipe_data.instructions)

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

    async def get_ingredients_by_meal_name(self, user_id: int, meal: str) -> list[str] | None:
        query = select(Recipe).filter_by(user_id=user_id, meal_name=meal)
        result = await self.db.execute(query)
        recipe = result.scalar_one_or_none()
        return json.loads(recipe.ingredients) if recipe else None
