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
    ingredients = ["Ingredient 1", "Ingredient 2", "Ingredient 3"]
    instructions = ["Step 1", "Step 2", "Step 3"]
    
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
    recipe_id = test_recipe.id
    
    response = await async_client.get(
        f"/recipe/{recipe_id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == "Test Recipe"
    assert data["meal_type"] == VALID_MEAL_TYPES[0]
    assert isinstance(data["ingredients"], list)
    assert len(data["ingredients"]) == 3
    assert "Ingredient 1" in data["ingredients"]
    assert isinstance(data["instructions"], list)
    assert len(data["instructions"]) == 3
    assert "Step 1" in data["instructions"]


@pytest.mark.asyncio
async def test_get_recipe_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test recipe retrieval with non-existent ID."""
    non_existent_id = 9999
    
    response = await async_client.get(
        f"/recipe/{non_existent_id}",
        headers=auth_headers
    )
    
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
    recipe_id = test_recipe.id
    
    response = await async_client.get(f"/recipe/{recipe_id}")
    
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
    another_user = TestUser(
        user_name="another_user",
        email="another@example.com",
        hash="hashedpassword"
    )
    db_session.add(another_user)
    await db_session.commit()
    await db_session.refresh(another_user)
    
    ingredients = ["Ingredient A", "Ingredient B"]
    instructions = ["Instruction A", "Instruction B"]
    
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
    
    response = await async_client.get(
        f"/recipe/{another_recipe.id}",
        headers=auth_headers
    )
    
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
    response = await async_client.get(
        "/recipe/invalid_id",
        headers=auth_headers
    )
    
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
    ingredients = ["Wheat flour", "Powdered sugar", "Butter 82%", "Fresh eggs"]
    instructions = [
        "Mix the ingredients",
        "Bake at 180°C for 30 minutes",
        "Dust with powdered sugar & decorate"
    ]
    
    recipe = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Cake with chocolate glaze",
        meal_type=VALID_MEAL_TYPES[3],  # dessert
        ingredients=json.dumps(ingredients),
        instructions=json.dumps(instructions)
    )
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    
    response = await async_client.get(
        f"/recipe/{recipe.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == "Cake with chocolate glaze"
    assert data["meal_type"] == VALID_MEAL_TYPES[3]
    assert "Wheat flour" in data["ingredients"]
    assert "Butter 82%" in data["ingredients"]
    assert "Bake at 180°C for 30 minutes" in data["instructions"]
    assert "Dust with powdered sugar & decorate" in data["instructions"]


@pytest.mark.asyncio
async def test_get_recipe_nonexistent_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test retrieving a recipe with an ID that doesn't exist."""
    nonexistent_id = 99999
    
    response = await async_client.get(
        f"/recipe/{nonexistent_id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert "detail" in response_data
    assert "Recipe not found" in response_data["detail"]