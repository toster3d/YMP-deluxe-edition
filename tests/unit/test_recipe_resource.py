from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from src.resources.pydantic_schemas import RecipeSchema, RecipeUpdateSchema
from src.resources.recipe_resource import RecipeListResource, RecipeResource


@pytest.fixture
def recipe_manager() -> AsyncMock:
    """Fixture providing a mock for the recipe manager."""
    manager = AsyncMock()
    return manager


@pytest.fixture
def recipe_list_resource(recipe_manager: AsyncMock) -> RecipeListResource:
    """Fixture providing a RecipeListResource instance with a mock recipe manager."""
    resource = RecipeListResource()
    resource.recipe_manager = recipe_manager
    return resource


@pytest.fixture
def recipe_resource(recipe_manager: AsyncMock) -> RecipeResource:
    """Fixture providing a RecipeResource instance with a mock recipe manager."""
    resource = RecipeResource()
    resource.recipe_manager = recipe_manager
    return resource


class TestRecipeListResource:
    """Test suite for RecipeListResource."""

    class TestGet:
        """Tests for the get method of RecipeListResource."""

        @pytest.mark.asyncio
        async def test_get_empty(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method when no recipes are found."""
            user_id = 1
            recipe_manager.get_recipes.return_value = []
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_list_resource.get(user_id)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "No recipes found for this user" in exc_info.value.detail
            recipe_manager.get_recipes.assert_called_once_with(user_id)

        @pytest.mark.asyncio
        async def test_get_success(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method with recipes."""
            user_id = 1
            mock_recipes = [
                RecipeSchema(
                    meal_name="Test Recipe 1",
                    meal_type="breakfast",
                    ingredients=[],
                    instructions=[]
                ),
                RecipeSchema(
                    meal_name="Test Recipe 2",
                    meal_type="lunch",
                    ingredients=[],
                    instructions=[]
                )
            ]
            recipe_manager.get_recipes.return_value = mock_recipes
            
            result = await recipe_list_resource.get(user_id)
            
            assert result == {"recipes": mock_recipes}
            recipe_manager.get_recipes.assert_called_once_with(user_id)

        @pytest.mark.asyncio
        async def test_get_with_manager_error(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method when recipe_manager raises an error."""
            user_id = 1
            recipe_manager.get_recipes.side_effect = Exception("Database error")
            
            with pytest.raises(Exception) as exc_info:
                await recipe_list_resource.get(user_id)
            
            assert str(exc_info.value) == "Database error"
            recipe_manager.get_recipes.assert_called_once_with(user_id)

    class TestPost:
        """Tests for the post method of RecipeListResource."""

        @pytest.mark.asyncio
        async def test_post_success(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test post method for adding a recipe successfully."""
            user_id = 1
            recipe_data = RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            mock_recipe = MagicMock()
            mock_recipe.id = 1
            mock_recipe.meal_name = recipe_data.meal_name
            mock_recipe.meal_type = recipe_data.meal_type
            
            recipe_manager.add_recipe.return_value = mock_recipe
            
            result = await recipe_list_resource.post(recipe_data, user_id)
            
            assert result["message"] == "Recipe added successfully!"
            assert result["recipe_id"] == mock_recipe.id
            assert result["meal_name"] == mock_recipe.meal_name
            assert result["meal_type"] == mock_recipe.meal_type
            
            recipe_manager.add_recipe.assert_called_once_with(recipe_data=recipe_data, user_id=user_id)

        @pytest.mark.asyncio
        async def test_post_error(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test post method with an error."""
            user_id = 1
            recipe_data = RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            error_message = "Database error"
            recipe_manager.add_recipe.side_effect = Exception(error_message)
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_list_resource.post(recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert f"Failed to add recipe: {error_message}" in exc_info.value.detail
            recipe_manager.add_recipe.assert_called_once_with(recipe_data=recipe_data, user_id=user_id)

        @pytest.mark.asyncio
        async def test_post_specific_exception(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test post method with a specific type of exception."""
            user_id = 1
            recipe_data = RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            error_message = "Invalid value"
            recipe_manager.add_recipe.side_effect = ValueError(error_message)
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_list_resource.post(recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert f"Failed to add recipe: {error_message}" in exc_info.value.detail

        @pytest.mark.asyncio
        async def test_post_http_exception_passthrough(
            self, recipe_list_resource: RecipeListResource, recipe_manager: AsyncMock
        ) -> None:
            """Test that HTTPException from recipe_manager is passed through."""
            user_id = 1
            recipe_data = RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            http_exception = HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Recipe already exists"
            )
            recipe_manager.add_recipe.side_effect = http_exception
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_list_resource.post(recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to add recipe" in exc_info.value.detail


class TestRecipeResource:
    """Test suite for RecipeResource."""

    class TestGet:
        """Tests for the get method of RecipeResource."""

        @pytest.mark.asyncio
        async def test_get_not_found(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method when recipe is not found."""
            recipe_id = 1
            user_id = 1
            recipe_manager.get_recipe_details.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.get(recipe_id, user_id)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Recipe not found" in exc_info.value.detail
            recipe_manager.get_recipe_details.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_get_success(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method with a found recipe."""
            recipe_id = 1
            user_id = 1
            mock_recipe = RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            recipe_manager.get_recipe_details.return_value = mock_recipe
            
            result = await recipe_resource.get(recipe_id, user_id)
            
            assert result == mock_recipe
            recipe_manager.get_recipe_details.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_get_with_database_error(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test get method with a database error."""
            recipe_id = 1
            user_id = 1
            recipe_manager.get_recipe_details.side_effect = Exception("Database error")
            
            with pytest.raises(Exception) as exc_info:
                await recipe_resource.get(recipe_id, user_id)
            
            assert str(exc_info.value) == "Database error"
            recipe_manager.get_recipe_details.assert_called_once_with(recipe_id, user_id)

    class TestPatch:
        """Tests for the patch method of RecipeResource."""

        @pytest.mark.asyncio
        async def test_patch_not_found(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method when recipe is not found."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch"
            )
            
            recipe_manager.update_recipe.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Recipe not found" in exc_info.value.detail
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )
            recipe_manager.get_recipe_by_id.assert_not_called()

        @pytest.mark.asyncio
        async def test_patch_not_found_after_update(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method when recipe is not found after update."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch"
            )
            
            recipe_manager.update_recipe.return_value = True
            recipe_manager.get_recipe_by_id.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Recipe not found after update" in exc_info.value.detail
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )
            recipe_manager.get_recipe_by_id.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_patch_success(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method with successful update."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch"
            )
            
            mock_updated_recipe = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            recipe_manager.update_recipe.return_value = True
            recipe_manager.get_recipe_by_id.return_value = mock_updated_recipe
            
            result = await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert result == mock_updated_recipe
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )
            recipe_manager.get_recipe_by_id.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_patch_error(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method with an error."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch"
            )
            
            error_message = "Database error"
            recipe_manager.update_recipe.side_effect = Exception(error_message)
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert f"Failed to update recipe: {error_message}" in exc_info.value.detail
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )

        @pytest.mark.asyncio
        async def test_patch_with_http_exception(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method when recipe_manager raises HTTPException."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema(
                meal_name="Updated Recipe",
                meal_type="lunch"
            )
            
            http_exception = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad request"
            )
            recipe_manager.update_recipe.side_effect = http_exception
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert exc_info.value == http_exception
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )

        @pytest.mark.asyncio
        async def test_patch_with_empty_data(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test patch method with empty update data."""
            recipe_id = 1
            user_id = 1
            recipe_data = RecipeUpdateSchema()
            
            mock_updated_recipe = RecipeUpdateSchema(
                meal_name="Original Recipe",
                meal_type="breakfast",
                ingredients=["ingredient1", "ingredient2"],
                instructions=["step1", "step2"]
            )
            
            recipe_manager.update_recipe.return_value = True
            recipe_manager.get_recipe_by_id.return_value = mock_updated_recipe
            
            result = await recipe_resource.patch(recipe_id, recipe_data, user_id)
            
            assert result == mock_updated_recipe
            recipe_manager.update_recipe.assert_called_once_with(
                recipe_id=recipe_id, user_id=user_id, recipe_data=recipe_data
            )
            recipe_manager.get_recipe_by_id.assert_called_once_with(recipe_id, user_id)

    class TestDelete:
        """Tests for the delete method of RecipeResource."""

        @pytest.mark.asyncio
        async def test_delete_not_found(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test delete method when recipe is not found."""
            recipe_id = 1
            user_id = 1
            recipe_manager.delete_recipe.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.delete(recipe_id, user_id)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Recipe not found" in exc_info.value.detail
            recipe_manager.delete_recipe.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_delete_success(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test delete method with successful deletion."""
            recipe_id = 1
            user_id = 1
            recipe_manager.delete_recipe.return_value = True
            
            await recipe_resource.delete(recipe_id, user_id)
            
            recipe_manager.delete_recipe.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_delete_error(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test delete method with an error."""
            recipe_id = 1
            user_id = 1
            error_message = "Database error"
            recipe_manager.delete_recipe.side_effect = Exception(error_message)
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.delete(recipe_id, user_id)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert f"Failed to delete recipe: {error_message}" in exc_info.value.detail
            recipe_manager.delete_recipe.assert_called_once_with(recipe_id, user_id)

        @pytest.mark.asyncio
        async def test_delete_with_http_exception(
            self, recipe_resource: RecipeResource, recipe_manager: AsyncMock
        ) -> None:
            """Test delete method when recipe_manager raises HTTPException."""
            recipe_id = 1
            user_id = 1
            http_exception = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad request"
            )
            recipe_manager.delete_recipe.side_effect = http_exception
            
            with pytest.raises(HTTPException) as exc_info:
                await recipe_resource.delete(recipe_id, user_id)
            
            assert exc_info.value == http_exception
            recipe_manager.delete_recipe.assert_called_once_with(recipe_id, user_id)

