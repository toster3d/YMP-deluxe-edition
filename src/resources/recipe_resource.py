from typing import Any

from fastapi import HTTPException, status
from pydantic_schemas import RecipeSchema, RecipeUpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession

from services.recipe_manager import RecipeDict, RecipeManager


class RecipeListResource:
    """Resource for handling recipe collections."""
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize resource with database session."""
        self.recipe_manager = RecipeManager(db)

    async def get(self, user_id: int) -> dict[str, list[RecipeDict]]:
        """Get all recipes for a user."""
        recipes = await self.recipe_manager.get_recipes(user_id)
        
        if not recipes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recipes found for this user."
            )
            
        return {"recipes": recipes}

    async def post(self, recipe_data: RecipeSchema, user_id: int) -> dict[str, Any]:
        """Create a new recipe."""
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
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize resource with database session."""
        self.recipe_manager = RecipeManager(db)

    async def get(self, recipe_id: int, user_id: int) -> RecipeDict:
        """Get a specific recipe."""
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
    ) -> RecipeDict | None:
        """
        Update a specific recipe.
        
        Args:
            recipe_id: ID of the recipe
            recipe_data: Recipe update data
            
        Returns:
            dict: Updated recipe details
            
        Raises:
            HTTPException: If recipe update fails
        """
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
                
            return await self.recipe_manager.get_recipe_by_id(recipe_id, user_id)
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
