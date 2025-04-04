import json
import logging

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_models.models_db_test import TestRecipe, TestUser

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
class TestRecipeGetRoute:
    """Tests for GET /recipe endpoint."""
    
    class TestSuccessScenarios:
        """Tests for successful recipe retrieval scenarios."""
        
        async def test_get_recipes_success(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test successful retrieval of recipes."""
            test_recipes = [
                TestRecipe(
                    user_id=create_test_user.id,
                    meal_name="Test Recipe 1",
                    meal_type="dinner",
                    ingredients=json.dumps(["ingredient1", "ingredient2"]),
                    instructions=json.dumps(["step1", "step2"])
                ),
                TestRecipe(
                    user_id=create_test_user.id,
                    meal_name="Test Recipe 2",
                    meal_type="breakfast",
                    ingredients=json.dumps(["ingredient3", "ingredient4"]),
                    instructions=json.dumps(["step3", "step4"])
                )
            ]
            
            for recipe in test_recipes:
                db_session.add(recipe)
            
            await db_session.commit()
            
            response = await async_client.get("/recipe", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert "recipes" in response_data
            assert len(response_data["recipes"]) == 2
            
            recipes = response_data["recipes"]
            recipe_names = [r["meal_name"] for r in recipes]
            assert "Test Recipe 1" in recipe_names
            assert "Test Recipe 2" in recipe_names
            
            for recipe in recipes:
                if recipe["meal_name"] == "Test Recipe 1":
                    assert recipe["meal_type"] == "dinner"
                    assert "ingredient1" in recipe["ingredients"]
                    assert "step1" in recipe["instructions"]
                elif recipe["meal_name"] == "Test Recipe 2":
                    assert recipe["meal_type"] == "breakfast"
                    assert "ingredient3" in recipe["ingredients"]
                    assert "step3" in recipe["instructions"]

    class TestErrorScenarios:
        """Tests for error scenarios."""
        
        async def test_get_recipes_empty(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser
        ) -> None:
            """Test response when user has no recipes."""
            response = await async_client.get("/recipe", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            response_data = response.json()
            assert "detail" in response_data
            assert response_data["detail"] == "No recipes found for this user."

        async def test_get_recipes_unauthorized(
            self,
            async_client: AsyncClient
        ) -> None:
            """Test accessing recipes without authentication."""
            response = await async_client.get("/recipe")
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response_data = response.json()
            assert "detail" in response_data
            assert response_data["detail"] == "Not authenticated"

    class TestIsolationScenarios:
        """Tests for data isolation between users."""
        
        async def test_get_recipes_other_user(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test that a user cannot see recipes from another user."""
            other_user = TestUser(
                user_name="other_user",
                email="other@example.com",
                hash="hashedpassword"
            )
            db_session.add(other_user)
            await db_session.commit()
            await db_session.refresh(other_user)
            
            other_recipe = TestRecipe(
                user_id=other_user.id,
                meal_name="Other User Recipe",
                meal_type="lunch",
                ingredients=json.dumps(["other ingredient"]),
                instructions=json.dumps(["other step"])
            )
            db_session.add(other_recipe)
            await db_session.commit()
            
            response = await async_client.get("/recipe", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            await db_session.delete(other_user)
            await db_session.commit()

        async def test_get_recipes_with_multiple_users(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test that each user only sees their own recipes."""
            other_user = TestUser(
                user_name="multi_user",
                email="multi@example.com",
                hash="hashedpassword"
            )
            db_session.add(other_user)
            await db_session.commit()
            await db_session.refresh(other_user)
            
            test_recipes = [
                TestRecipe(
                    user_id=create_test_user.id,
                    meal_name="Current User Recipe",
                    meal_type="dinner",
                    ingredients=json.dumps(["current ingredient"]),
                    instructions=json.dumps(["current step"])
                ),
                TestRecipe(
                    user_id=other_user.id,
                    meal_name="Other User Recipe",
                    meal_type="lunch",
                    ingredients=json.dumps(["other ingredient"]),
                    instructions=json.dumps(["other step"])
                )
            ]
            
            for recipe in test_recipes:
                db_session.add(recipe)
            
            await db_session.commit()
            
            response = await async_client.get("/recipe", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert "recipes" in response_data
            
            assert len(response_data["recipes"]) == 1
            assert response_data["recipes"][0]["meal_name"] == "Current User Recipe"
            
            await db_session.delete(other_user)
            await db_session.commit()

    class TestResponseValidation:
        """Tests for response format and content validation."""
        
        async def test_recipe_response_format(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test that recipe response follows the expected schema."""
            test_recipe = TestRecipe(
                user_id=create_test_user.id,
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=json.dumps(["ingredient1", "ingredient2"]),
                instructions=json.dumps(["step1", "step2"])
            )
            db_session.add(test_recipe)
            await db_session.commit()
            
            response = await async_client.get("/recipe", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "recipes" in data
            recipe = data["recipes"][0]
            assert all(key in recipe for key in [
                "meal_name",
                "meal_type",
                "ingredients",
                "instructions"
            ])
            
            assert isinstance(recipe["meal_name"], str)
            assert isinstance(recipe["meal_type"], str)
            assert isinstance(recipe["ingredients"], list)
            assert isinstance(recipe["instructions"], list)
            
            assert recipe["meal_name"] == "Test Recipe"
            assert recipe["meal_type"] == "breakfast"
            assert recipe["ingredients"] == ["ingredient1", "ingredient2"]
            assert recipe["instructions"] == ["step1", "step2"]