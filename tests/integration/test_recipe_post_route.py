import json

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.mark.asyncio
class TestRecipePostRoute:
    """Tests for POST /recipe endpoint."""
    
    class TestSuccessScenarios:
        """Tests for successful recipe creation scenarios."""
        
        async def test_create_recipe_success(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test successful recipe creation."""
            recipe_data = {
                "meal_name": "Test Recipe",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            response_data = response.json()
            assert "message" in response_data
            assert response_data["message"] == "Recipe added successfully!"
            assert "recipe_id" in response_data
            assert "meal_name" in response_data
            assert response_data["meal_name"] == "Test Recipe"
            assert "meal_type" in response_data
            assert response_data["meal_type"] == "dinner"
            
            recipe_id = response_data["recipe_id"]
            query = select(TestRecipe).filter_by(id=recipe_id)
            result = await db_session.execute(query)
            recipe = result.scalar_one_or_none()
            
            assert recipe is not None
            assert recipe.meal_name == "Test Recipe"
            assert recipe.meal_type == "dinner"
            assert json.loads(recipe.ingredients) == ["Ingredient 1", "Ingredient 2"]
            assert json.loads(recipe.instructions) == ["Step 1", "Step 2"]
            assert recipe.user_id == create_test_user.id

        async def test_create_recipe_with_special_characters(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test recipe creation with allowed special characters."""
            recipe_data = {
                "meal_name": "Grandma's Special-Recipe 123",
                "meal_type": "dinner",
                "ingredients": ["400g flour", "4 eggs", "100ml water"],
                "instructions": ["Mix ingredients", "Cook for 30 minutes", "Serve hot"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            query = select(TestRecipe).filter_by(
                user_id=create_test_user.id,
                meal_name="Grandma's Special-Recipe 123"
            )
            result = await db_session.execute(query)
            recipe = result.scalar_one_or_none()
            
            assert recipe is not None
            assert recipe.meal_name == "Grandma's Special-Recipe 123"
            assert recipe.meal_type == "dinner"
            assert "400g flour" in json.loads(recipe.ingredients)
            assert "Mix ingredients" in json.loads(recipe.instructions)

        async def test_create_recipe_with_invalid_special_characters(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with disallowed special characters."""
            recipe_data = {
                "meal_name": "Recipe & Sauce",  # & is not allowed
                "meal_type": "dinner",
                "ingredients": ["ingredient 1"],
                "instructions": ["step 1"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(
                "String should match pattern" in error["msg"] 
                for error in errors
            )

        async def test_create_recipe_with_unicode_characters(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with unicode characters (should be rejected)."""
            recipe_data = {
                "meal_name": "寿司 Sushi",  # Contains non-Latin characters
                "meal_type": "dinner",
                "ingredients": ["rice", "fish", "nori"],
                "instructions": ["prepare", "roll", "cut"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(
                "String should match pattern" in error["msg"] 
                for error in errors
            )

        async def test_create_recipe_with_accented_characters(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with accented characters (should be rejected)."""
            recipe_data = {
                "meal_name": "Café au lait",  # Contains accented character
                "meal_type": "breakfast",
                "ingredients": ["coffee", "milk"],
                "instructions": ["brew coffee", "add milk"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(
                "String should match pattern" in error["msg"] 
                for error in errors
            )

    class TestValidationScenarios:
        """Tests for input validation scenarios."""
        
        async def test_create_recipe_invalid_meal_type(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with invalid meal type."""
            recipe_data = {
                "meal_name": "Test Recipe",
                "meal_type": "invalid_type",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(error["loc"][1] == "meal_type" for error in errors)

        async def test_create_recipe_empty_meal_name(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with empty meal name."""
            recipe_data = {
                "meal_name": "",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(error["loc"][1] == "meal_name" for error in errors)

        async def test_create_recipe_empty_ingredient(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with empty ingredient."""
            recipe_data = {
                "meal_name": "Test Recipe",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", ""],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(error["loc"][1] == "ingredients" for error in errors)

        async def test_create_recipe_empty_instruction(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with empty instruction."""
            recipe_data = {
                "meal_name": "Test Recipe",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", ""]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(error["loc"][1] == "instructions" for error in errors)

        async def test_create_recipe_missing_required_fields(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with missing required fields."""
            recipe_data = {
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            missing_fields = [error["loc"][1] for error in errors]
            assert "meal_name" in missing_fields
            assert "meal_type" in missing_fields

        async def test_create_recipe_too_long_meal_name(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str]
        ) -> None:
            """Test recipe creation with too long meal name."""
            recipe_data = {
                "meal_name": "A" * 201,
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            response_data = response.json()
            assert "detail" in response_data
            errors = response_data["detail"]
            assert any(error["loc"][1] == "meal_name" for error in errors)

        async def test_create_duplicate_recipe(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            create_test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test creating a recipe with the same name as an existing one."""
            recipe_data = {
                "meal_name": "Duplicate Recipe",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            first_response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            assert first_response.status_code == status.HTTP_201_CREATED
            
            second_response = await async_client.post(
                "/recipe",
                json=recipe_data,
                headers=auth_headers
            )
            
            assert second_response.status_code == status.HTTP_201_CREATED
            
            query = select(TestRecipe).filter_by(
                user_id=create_test_user.id, 
                meal_name="Duplicate Recipe"
            )
            result = await db_session.execute(query)
            recipes = result.scalars().all()
            
            assert len(recipes) == 2

    class TestErrorScenarios:
        """Tests for error handling scenarios."""
        
        async def test_create_recipe_unauthorized(
            self,
            async_client: AsyncClient
        ) -> None:
            """Test recipe creation without authentication."""
            recipe_data = {
                "meal_name": "Test Recipe",
                "meal_type": "dinner",
                "ingredients": ["Ingredient 1", "Ingredient 2"],
                "instructions": ["Step 1", "Step 2"]
            }
            
            response = await async_client.post(
                "/recipe",
                json=recipe_data
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response_data = response.json()
            assert "detail" in response_data