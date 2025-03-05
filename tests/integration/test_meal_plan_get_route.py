import json
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.fixture
async def test_recipes(
    db_session: AsyncSession,
    create_test_user: TestUser
) -> list[TestRecipe]:
    """Create several test recipes for the user."""
    recipes = [
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Oatmeal",
            meal_type="breakfast",
            ingredients=json.dumps(["Oats", "Milk", "Honey"]),
            instructions=json.dumps(["Cook the oats", "Add milk and honey"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Tuna Salad",
            meal_type="lunch",
            ingredients=json.dumps(["Lettuce", "Tuna", "Tomato", "Olive oil"]),
            instructions=json.dumps(["Chop the vegetables", "Add tuna", "Drizzle with olive oil"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Spaghetti Bolognese",
            meal_type="dinner",
            ingredients=json.dumps(["Pasta", "Ground meat", "Tomatoes", "Onion"]),
            instructions=json.dumps(["Cook the pasta", "Prepare the sauce", "Combine ingredients"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Cheesecake",
            meal_type="dessert",
            ingredients=json.dumps(["Cottage cheese", "Eggs", "Sugar", "Butter"]),
            instructions=json.dumps(["Prepare the cheese mixture", "Bake the cake"])
        )
    ]
    
    for recipe in recipes:
        db_session.add(recipe)
    
    await db_session.commit()
    
    # Refresh objects to get assigned IDs
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    return recipes


@pytest.mark.asyncio
async def test_get_meal_plan_options_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipes: list[TestRecipe]
) -> None:
    """Test successful retrieval of meal plan options."""
    # Act
    response = await async_client.get(
        "/meal_plan",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    
    assert "recipes" in response_data
    recipes: list[dict[str, Any]] = response_data["recipes"]
    assert isinstance(recipes, list)
    assert len(recipes) == 4  # We have 4 test recipes
    
    # Check if all expected recipes are present
    recipe_names = [recipe["name"] for recipe in recipes]
    expected_names = ["Oatmeal", "Tuna Salad", "Spaghetti Bolognese", "Cheesecake"]
    assert set(recipe_names) == set(expected_names)
    
    # Check the structure of recipe data
    for recipe in recipes:
        assert "id" in recipe
        assert "name" in recipe
        assert "meal_type" in recipe
        assert recipe["meal_type"] in ["breakfast", "lunch", "dinner", "dessert"]


@pytest.mark.asyncio
async def test_get_meal_plan_options_no_recipes(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession
) -> None:
    """Test retrieval of meal plan options when user has no recipes."""
    # Delete all recipes (if they exist)
    await db_session.execute(delete(TestRecipe))
    await db_session.commit()
    
    # Act
    response = await async_client.get(
        "/meal_plan",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    
    assert "recipes" in response_data
    recipes: list[dict[str, Any]] = response_data["recipes"]
    assert isinstance(recipes, list)
    assert len(recipes) == 0  # Empty list of recipes

@pytest.mark.asyncio
async def test_get_meal_plan_options_unauthorized(
    async_client: AsyncClient
) -> None:
    """Test attempts to retrieve meal plan options without authorization."""
    # Act
    response = await async_client.get("/meal_plan")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_meal_plan_options_with_invalid_token(
    async_client: AsyncClient
) -> None:
    """Test attempts to retrieve meal plan options with an invalid token."""
    # Act
    invalid_headers = {"Authorization": "Bearer invalid.token.here"}
    response = await async_client.get(
        "/meal_plan",
        headers=invalid_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_meal_plan_options_check_recipe_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipes: list[TestRecipe]
) -> None:
    """Test checking the exact structure of returned recipe data."""
    # Act
    response = await async_client.get(
        "/meal_plan",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    
    recipes = response_data["recipes"]
    assert len(recipes) > 0
    
    # Check the first recipe
    first_recipe = recipes[0]
    assert isinstance(first_recipe["id"], int)
    assert isinstance(first_recipe["name"], str)
    assert isinstance(first_recipe["meal_type"], str)
    
    # Find the recipe in the original list
    original_recipe = next((r for r in test_recipes if r.id == first_recipe["id"]), None)
    assert original_recipe is not None
    
    # Compare data
    assert first_recipe["name"] == original_recipe.meal_name
    assert first_recipe["meal_type"] == original_recipe.meal_type 