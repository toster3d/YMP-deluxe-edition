from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from extensions import get_async_db
from services.recipe_manager import RecipeDict, RecipeManager

from .pydantic_schemas import RecipeSchema, RecipeUpdateSchema


class RecipeListResource:
    """Resource for handling recipe collections."""
    
    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize resource with database session."""
        self.recipe_manager = RecipeManager(db)

    async def get(self, user_id: int) -> dict[str, list[RecipeDict]]:
        """
        Get all recipes for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: List of user's recipes
            
        Raises:
            HTTPException: If no recipes found
        """
        recipes = await self.recipe_manager.get_recipes(user_id)
        
        if not recipes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recipes found for this user."
            )
            
        return {"recipes": recipes}

    async def post(self, recipe_data: RecipeSchema, user_id: int) -> dict[str, Any]:
        """
        Create a new recipe.
        
        Args:
            recipe_data: Recipe data
            user_id: ID of the user
            
        Returns:
            dict: Created recipe details
            
        Raises:
            HTTPException: If recipe creation fails
        """
        try:
            recipe = await self.recipe_manager.add_recipe(
                user_id=user_id,
                meal_name=recipe_data.meal_name,
                meal_type=recipe_data.meal_type,
                ingredients=recipe_data.ingredients,
                instructions=recipe_data.instructions
            )
            
            return {
                "message": "Recipe added successfully!",
                "recipe_id": recipe.id,
                "meal_name": recipe.meal_name,
                "meal_type": recipe.meal_type
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add recipe: {str(e)}"
            )


class RecipeResource:
    """Resource for handling individual recipes."""
    
    def __init__(self, db: AsyncSession = Depends(get_async_db)) -> None:
        """Initialize resource with database session."""
        self.recipe_manager = RecipeManager(db)

    async def get(self, recipe_id: int, user_id: int) -> RecipeDict:
        """
        Get a specific recipe.
        
        Args:
            recipe_id: ID of the recipe
            user_id: ID of the user
            
        Returns:
            RecipeDict: Recipe details
            
        Raises:
            HTTPException: If recipe not found
        """
        recipe = await self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        return recipe

    async def patch(
        self, 
        recipe_id: int, 
        recipe_data: RecipeUpdateSchema,
        user_id: int
    ) -> RecipeDict:
        """Update a specific recipe."""
        try:
            updated_recipe = await self.recipe_manager.update_recipe(
                recipe_id=recipe_id,
                user_id=user_id,
                meal_name=recipe_data.meal_name,
                meal_type=recipe_data.meal_type,
                ingredients=recipe_data.ingredients,
                instructions=recipe_data.instructions
            )
            
            if not updated_recipe:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recipe not found"
                )
            
            result = await self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recipe not found after update"
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update recipe: {str(e)}"
            )

    async def delete(self, recipe_id: int, user_id: int) -> None:
        """
        Delete a specific recipe.
        
        Args:
            recipe_id: ID of the recipe
            user_id: ID of the user
            
        Raises:
            HTTPException: If recipe deletion fails
        """
        try:
            if not await self.recipe_manager.delete_recipe(recipe_id, user_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recipe not found"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete recipe: {str(e)}"
            )
