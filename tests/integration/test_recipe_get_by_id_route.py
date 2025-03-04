import json
import logging

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.resources.pydantic_schemas import VALID_MEAL_TYPES
from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.fixture
async def test_recipe(db_session: AsyncSession, create_test_user: TestUser) -> TestRecipe:
    """Fixture creating a test recipe."""
    ingredients = ["Składnik 1", "Składnik 2", "Składnik 3"]
    instructions = ["Krok 1", "Krok 2", "Krok 3"]
    
    recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Recipe",
        meal_type=VALID_MEAL_TYPES[0],  # breakfast
        ingredients=json.dumps(ingredients),
        instructions=json.dumps(instructions)
    )
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    
    logging.info(f"Created test recipe with ID: {recipe.id}")
    return recipe


@pytest.mark.asyncio
async def test_get_recipe_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test successful recipe retrieval."""
    # Arrange
    recipe_id = test_recipe.id
    
    # Act
    response = await async_client.get(
        f"/recipe/{recipe_id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == "Test Recipe"
    assert data["meal_type"] == VALID_MEAL_TYPES[0]
    assert isinstance(data["ingredients"], list)
    assert len(data["ingredients"]) == 3
    assert "Składnik 1" in data["ingredients"]
    assert isinstance(data["instructions"], list)
    assert len(data["instructions"]) == 3
    assert "Krok 1" in data["instructions"]


@pytest.mark.asyncio
async def test_get_recipe_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe retrieval with non-existent ID."""
    # Arrange
    non_existent_id = 9999
    
    # Act
    response = await async_client.get(
        f"/recipe/{non_existent_id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Recipe not found"


@pytest.mark.asyncio
async def test_get_recipe_unauthorized(
    async_client: AsyncClient,
    test_recipe: TestRecipe
) -> None:
    """Test recipe retrieval without authentication."""
    # Arrange
    recipe_id = test_recipe.id
    
    # Act
    response = await async_client.get(f"/recipe/{recipe_id}")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_recipe_from_another_user(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession
) -> None:
    """Test retrieving a recipe that belongs to another user."""
    # Arrange - Create another user and their recipe
    another_user = TestUser(
        user_name="another_user",
        email="another@example.com",
        hash="hashedpassword"
    )
    db_session.add(another_user)
    await db_session.commit()
    await db_session.refresh(another_user)
    
    # Create recipe for another user
    ingredients = ["Składnik A", "Składnik B"]
    instructions = ["Instrukcja A", "Instrukcja B"]
    
    another_recipe = TestRecipe(
        user_id=another_user.id,
        meal_name="Another User Recipe",
        meal_type=VALID_MEAL_TYPES[1],  # lunch
        ingredients=json.dumps(ingredients),
        instructions=json.dumps(instructions)
    )
    
    db_session.add(another_recipe)
    await db_session.commit()
    await db_session.refresh(another_recipe)
    
    # Act - Try to access another user's recipe
    response = await async_client.get(
        f"/recipe/{another_recipe.id}",
        headers=auth_headers
    )
    
    # Assert - Should return 404 Not Found (not 403 Forbidden to prevent user enumeration)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Recipe not found"


@pytest.mark.asyncio
async def test_get_recipe_invalid_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe retrieval with invalid ID format."""
    # Act
    response = await async_client.get(
        "/recipe/invalid_id",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_recipe_with_special_characters(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    create_test_user: TestUser
) -> None:
    """Test retrieving a recipe with special characters in its content."""
    # Arrange
    ingredients = ["Mąka pszenna", "Cukier puder", "Masło 82%", "Jajka (świeże)"]
    instructions = [
        "Wymieszaj składniki",
        "Piecz w 180°C przez 30 minut",
        "Posyp cukrem pudrem & udekoruj"
    ]
    
    recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Ciasto z polewą czekoladową",
        meal_type=VALID_MEAL_TYPES[3],  # dessert
        ingredients=json.dumps(ingredients),
        instructions=json.dumps(instructions)
    )
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    
    # Act
    response = await async_client.get(
        f"/recipe/{recipe.id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == "Ciasto z polewą czekoladową"
    assert data["meal_type"] == VALID_MEAL_TYPES[3]
    assert "Mąka pszenna" in data["ingredients"]
    assert "Masło 82%" in data["ingredients"]
    assert "Piecz w 180°C przez 30 minut" in data["instructions"]
    assert "Posyp cukrem pudrem & udekoruj" in data["instructions"]