import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.fixture
async def test_recipe_for_deletion(
    db_session: AsyncSession, 
    create_test_user: TestUser
) -> TestRecipe:
    """Create a test recipe for deletion."""
    recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Recipe to Delete",
        meal_type="dinner",
        ingredients='["Ingredient 1", "Ingredient 2"]',
        instructions='["Step 1", "Step 2"]'
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest.fixture
async def another_user_recipe(
    db_session: AsyncSession
) -> TestRecipe:
    """Create a recipe owned by another user."""
    other_user = TestUser(
        user_name="OtherUser",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    recipe = TestRecipe(
        user_id=other_user.id,
        meal_name="Other User's Recipe",
        meal_type="breakfast",
        ingredients='["Ingredient 1", "Ingredient 2"]',
        instructions='["Step 1", "Step 2"]'
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest.mark.asyncio
class TestRecipeDeleteRoute:
    """Tests for DELETE /recipe/{recipe_id} endpoint."""

    class TestSuccessScenarios:
        """Tests for successful recipe deletion scenarios."""

        async def test_delete_recipe_success(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe_for_deletion: TestRecipe,
            db_session: AsyncSession
        ) -> None:
            """Test successful deletion of a recipe."""
            recipe_id = test_recipe_for_deletion.id
            
            response = await async_client.delete(
                f"/recipe/{recipe_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            
            query = select(TestRecipe).filter_by(id=recipe_id)
            result = await db_session.execute(query)
            recipe = result.scalar_one_or_none()
            assert recipe is None

    class TestErrorScenarios:
        """Tests for error handling scenarios."""

        async def test_delete_nonexistent_recipe(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test attempt to delete a nonexistent recipe."""
            nonexistent_recipe_id = 9999
            
            response = await async_client.delete(
                f"/recipe/{nonexistent_recipe_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            response_data = response.json()
            assert "detail" in response_data
            assert response_data["detail"] == "Recipe not found"

        async def test_delete_recipe_unauthorized(
            self,
            async_client: AsyncClient,
            test_recipe_for_deletion: TestRecipe
        ) -> None:
            """Test attempt to delete a recipe without authorization."""
            recipe_id = test_recipe_for_deletion.id
            
            response = await async_client.delete(
                f"/recipe/{recipe_id}"
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response_data = response.json()
            assert "detail" in response_data

        async def test_delete_other_users_recipe(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            another_user_recipe: TestRecipe,
            db_session: AsyncSession
        ) -> None:
            """Test attempt to delete a recipe owned by another user."""
            recipe_id = another_user_recipe.id
            
            response = await async_client.delete(
                f"/recipe/{recipe_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            response_data = response.json()
            assert "detail" in response_data
            assert response_data["detail"] == "Recipe not found"
            
            query = select(TestRecipe).filter_by(id=recipe_id)
            result = await db_session.execute(query)
            recipe = result.scalar_one_or_none()
            assert recipe is not None

        async def test_delete_recipe_invalid_id(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test attempt to delete a recipe with an invalid ID."""
            response = await async_client.delete(
                "/recipe/invalid_id",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data 