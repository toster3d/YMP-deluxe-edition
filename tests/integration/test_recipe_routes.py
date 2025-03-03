import json

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_models.models_db_test import TestRecipe, TestUser

from src.services.recipe_manager import RecipeManager


@pytest.mark.asyncio
async def test_get_recipes_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser
) -> None:
    """Test GET /recipe when user has no recipes."""
    # Act
    response = await async_client.get("/recipe", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "No recipes found for this user."


@pytest.mark.asyncio
async def test_get_recipes_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test GET /recipe when user has recipes."""
    # Arrange - Create test recipes
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
    
    # Act
    response = await async_client.get("/recipe", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "recipes" in response_data
    assert len(response_data["recipes"]) == 2
    
    # Verify recipe data
    recipes = response_data["recipes"]
    recipe_names = [r["meal_name"] for r in recipes]
    assert "Test Recipe 1" in recipe_names
    assert "Test Recipe 2" in recipe_names
    
    # Check specific recipe details
    for recipe in recipes:
        if recipe["meal_name"] == "Test Recipe 1":
            assert recipe["meal_type"] == "dinner"
            assert "ingredient1" in recipe["ingredients"]
            assert "step1" in recipe["instructions"]
        elif recipe["meal_name"] == "Test Recipe 2":
            assert recipe["meal_type"] == "breakfast"
            assert "ingredient3" in recipe["ingredients"]
            assert "step3" in recipe["instructions"]


@pytest.mark.asyncio
async def test_get_recipes_unauthorized(async_client: AsyncClient) -> None:
    """Test accessing recipes without authentication."""
    # Act
    response = await async_client.get("/recipe")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_recipes_other_user(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test that a user cannot see recipes from another user."""
    # Arrange - Create another user with recipes
    other_user = TestUser(
        user_name="other_user",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Add recipe for other user
    other_recipe = TestRecipe(
        user_id=other_user.id,
        meal_name="Other User Recipe",
        meal_type="lunch",
        ingredients=json.dumps(["other ingredient"]),
        instructions=json.dumps(["other step"])
    )
    db_session.add(other_recipe)
    await db_session.commit()
    
    # Act - Get recipes with authenticated user
    response = await async_client.get("/recipe", headers=auth_headers)
    
    # Assert - Should return 404 as the authenticated user has no recipes
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Clean up
    await db_session.delete(other_user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_recipe_manager_get_recipes(
    db_session: AsyncSession,
    create_test_user: TestUser
) -> None:
    """Test RecipeManager.get_recipes method directly."""
    # Arrange
    recipe_manager = RecipeManager(db_session)
    
    # Create test recipes
    test_recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Manager Test Recipe",
        meal_type="dessert",
        ingredients=json.dumps(["sugar", "flour"]),
        instructions=json.dumps(["mix", "bake"])
    )
    db_session.add(test_recipe)
    await db_session.commit()
    
    # Act
    recipes = await recipe_manager.get_recipes(create_test_user.id)
    
    # Assert
    assert len(recipes) == 1
    assert recipes[0].meal_name == "Manager Test Recipe"
    assert recipes[0].meal_type == "dessert"
    assert "sugar" in recipes[0].ingredients
    assert "mix" in recipes[0].instructions


@pytest.mark.asyncio
async def test_recipe_list_resource_get(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test RecipeListResource.get method through the API."""
    # Arrange - Create test recipe
    test_recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Resource Test Recipe",
        meal_type="breakfast",
        ingredients=json.dumps(["eggs", "milk"]),
        instructions=json.dumps(["scramble", "cook"])
    )
    db_session.add(test_recipe)
    await db_session.commit()
    
    # Act
    response = await async_client.get("/recipe", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "recipes" in response_data
    assert len(response_data["recipes"]) == 1
    
    recipe = response_data["recipes"][0]
    assert recipe["meal_name"] == "Resource Test Recipe"
    assert recipe["meal_type"] == "breakfast"
    assert "eggs" in recipe["ingredients"]
    assert "scramble" in recipe["instructions"]


@pytest.mark.asyncio
async def test_get_recipes_with_multiple_users(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    create_test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test that each user only sees their own recipes."""
    # Arrange - Create another user
    other_user = TestUser(
        user_name="multi_user",
        email="multi@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Add recipes for both users
    test_recipes = [
        # Current user's recipe
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Current User Recipe",
            meal_type="dinner",
            ingredients=json.dumps(["current ingredient"]),
            instructions=json.dumps(["current step"])
        ),
        # Other user's recipe
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
    
    # Act - Get recipes with authenticated user
    response = await async_client.get("/recipe", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "recipes" in response_data
    
    # Should only see current user's recipe
    assert len(response_data["recipes"]) == 1
    assert response_data["recipes"][0]["meal_name"] == "Current User Recipe"
    
    # Clean up
    await db_session.delete(other_user)
    await db_session.commit()
    
@pytest.mark.asyncio
async def test_get_recipes_malformed_token(async_client: AsyncClient) -> None:
    """Test behavior with malformed JWT token."""
    # Act
    response = await async_client.get(
        "/recipe", 
        headers={"Authorization": "Bearer invalid.token.format"}
    )
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_data = response.json()
    assert "detail" in response_data