import json

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.mark.asyncio
async def test_create_recipe_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test successful recipe creation."""
    # Arrange
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "message" in response_data
    assert response_data["message"] == "Recipe added successfully!"
    assert "recipe_id" in response_data
    assert "meal_name" in response_data
    assert response_data["meal_name"] == "Test Recipe"
    assert "meal_type" in response_data
    assert response_data["meal_type"] == "dinner"
    
    # Verify recipe was actually saved in the database
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


@pytest.mark.asyncio
async def test_create_recipe_unauthorized(
    async_client: AsyncClient
) -> None:
    """Test recipe creation without authentication."""
    # Arrange
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data
    )
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_data = response.json()
    assert "detail" in response_data


@pytest.mark.asyncio
async def test_create_recipe_invalid_meal_type(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with invalid meal type."""
    # Arrange
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "invalid_type",  # Invalid meal type
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błąd dotyczy pola meal_type
    errors = response_data["detail"]
    assert any(error["loc"][1] == "meal_type" for error in errors)


@pytest.mark.asyncio
async def test_create_recipe_empty_meal_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with empty meal name."""
    # Arrange
    recipe_data = {
        "meal_name": "",  # Empty meal name
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błąd dotyczy pola meal_name
    errors = response_data["detail"]
    assert any(error["loc"][1] == "meal_name" for error in errors)


@pytest.mark.asyncio
async def test_create_recipe_empty_ingredient(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with empty ingredient."""
    # Arrange
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", ""],  # Empty ingredient
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błąd dotyczy pola ingredients
    errors = response_data["detail"]
    assert any(error["loc"][1] == "ingredients" for error in errors)


@pytest.mark.asyncio
async def test_create_recipe_empty_instruction(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with empty instruction."""
    # Arrange
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", ""]  # Empty instruction
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błąd dotyczy pola instructions
    errors = response_data["detail"]
    assert any(error["loc"][1] == "instructions" for error in errors)


@pytest.mark.asyncio
async def test_create_recipe_missing_required_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with missing required fields."""
    # Arrange
    recipe_data = {
        # Missing meal_name and meal_type
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błędy dotyczą brakujących pól
    errors = response_data["detail"]
    missing_fields = [error["loc"][1] for error in errors]
    assert "meal_name" in missing_fields
    assert "meal_type" in missing_fields


@pytest.mark.asyncio
async def test_create_recipe_too_long_meal_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe creation with too long meal name."""
    # Arrange
    recipe_data = {
        "meal_name": "A" * 201,  # 201 characters (max is 200)
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Act
    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    # Sprawdzamy, czy błąd dotyczy pola meal_name
    errors = response_data["detail"]
    assert any(error["loc"][1] == "meal_name" for error in errors)


@pytest.mark.asyncio
async def test_create_duplicate_recipe(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test creating a recipe with the same name as an existing one."""
    # Arrange - Create first recipe
    recipe_data = {
        "meal_name": "Duplicate Recipe",
        "meal_type": "dinner",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": ["Step 1", "Step 2"]
    }
    
    # Add first recipe
    first_response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    assert first_response.status_code == status.HTTP_201_CREATED
    
    # Act - Try to add second recipe with same name
    second_response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    
    # Assert - This should still succeed as the API doesn't prevent duplicate recipe names
    assert second_response.status_code == status.HTTP_201_CREATED
    
    # Verify that we now have two recipes with the same name
    query = select(TestRecipe).filter_by(
        user_id=create_test_user.id, 
        meal_name="Duplicate Recipe"
    )
    result = await db_session.execute(query)
    recipes = result.scalars().all()
    
    assert len(recipes) == 2 