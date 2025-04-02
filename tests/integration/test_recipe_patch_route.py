import json
import logging
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.resources.pydantic_schemas import VALID_MEAL_TYPES
from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.fixture
async def test_recipe(
    db_session: AsyncSession,
    create_test_user: TestUser,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> TestRecipe:
    """Creates a test recipe for updating."""
    recipe_data = {
        "meal_name": "Test Recipe",
        "meal_type": "breakfast",
        "ingredients": ["Ingredient 1", "Ingredient 2", "Ingredient 3"],
        "instructions": ["Step 1", "Step 2", "Step 3"]
    }

    response = await async_client.post(
        "/recipe",
        json=recipe_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    recipe_id = response.json()["recipe_id"]
    
    query = select(TestRecipe).filter_by(id=recipe_id)
    result = await db_session.execute(query)
    recipe = result.scalar_one()
    
    logging.info(f"Created test recipe with ID: {recipe_id}")
    return recipe


@pytest.fixture
async def other_user_recipe(db_session: AsyncSession) -> TestRecipe:
    """Fixture creating a recipe owned by another user."""
    other_user = TestUser(
        user_name="other_user",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    ingredients = ["Ingredient A", "Ingredient B"]
    instructions = ["Instruction A", "Instruction B"]
    
    recipe = TestRecipe(
        user_id=other_user.id,
        meal_name="Other User Recipe",
        meal_type=VALID_MEAL_TYPES[1],  # lunch
        ingredients=json.dumps(ingredients),
        instructions=json.dumps(instructions)
    )
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    
    return recipe


@pytest.mark.asyncio
async def test_update_recipe_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating recipe name."""
    recipe_id = test_recipe.id
    new_name = "Updated Recipe Name"
    update_data = {"meal_name": new_name}
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == new_name
    
    await db_session.refresh(test_recipe)
    
    assert test_recipe.meal_name == new_name


@pytest.mark.asyncio
async def test_update_recipe_meal_type_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating the meal type in the recipe."""
    recipe_id = test_recipe.id
    update_data = {
        "meal_type": "dinner"
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_type"] == "dinner"
    
    await db_session.refresh(test_recipe)
    assert test_recipe.meal_type == "dinner"


@pytest.mark.asyncio
async def test_update_recipe_ingredients_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating the ingredients of the recipe."""
    recipe_id = test_recipe.id
    new_ingredients = ["New ingredient 1", "New ingredient 2", "New ingredient 3", "New ingredient 4"]
    update_data = {
        "ingredients": new_ingredients
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["ingredients"] == new_ingredients
    
    await db_session.refresh(test_recipe)
    ingredients_from_db = json.loads(test_recipe.ingredients)
    assert ingredients_from_db == new_ingredients


@pytest.mark.asyncio
async def test_update_recipe_instructions_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating the instructions of the recipe."""
    recipe_id = test_recipe.id
    new_instructions = ["New instruction 1", "New instruction 2", "New instruction 3"]
    update_data = {
        "instructions": new_instructions
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["instructions"] == new_instructions
    
    await db_session.refresh(test_recipe)
    instructions_from_db = json.loads(test_recipe.instructions)
    assert instructions_from_db == new_instructions


@pytest.mark.asyncio
async def test_update_recipe_all_fields_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating all fields of the recipe at once."""
    recipe_id = test_recipe.id
    update_data = {
        "meal_name": "Completely Updated Recipe",
        "meal_type": "dessert",
        "ingredients": ["Ingredient X", "Ingredient Y", "Ingredient Z"],
        "instructions": ["Instruction X", "Instruction Y", "Instruction Z"]
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == update_data["meal_name"]
    assert data["meal_type"] == update_data["meal_type"]
    assert data["ingredients"] == update_data["ingredients"]
    assert data["instructions"] == update_data["instructions"]
    
    await db_session.refresh(test_recipe)
    assert test_recipe.meal_name == update_data["meal_name"]
    assert test_recipe.meal_type == update_data["meal_type"]
    assert json.loads(test_recipe.ingredients) == update_data["ingredients"]
    assert json.loads(test_recipe.instructions) == update_data["instructions"]


@pytest.mark.asyncio
async def test_update_recipe_with_special_characters(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test updating a recipe using special characters."""
    recipe_id = test_recipe.id
    update_data: dict[str, Any] = {
        "meal_name": "Cake with chocolate glaze & fruits",
        "ingredients": ["Wheat flour", "Powdered sugar", "Butter 82%", "Eggs (fresh)"],
        "instructions": [
            "Mix the ingredients", 
            "Bake at 180°C for 30 minutes", 
            "Sprinkle with powdered sugar & decorate"
        ]
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["meal_name"] == update_data["meal_name"]
    assert data["ingredients"] == update_data["ingredients"]
    assert data["instructions"] == update_data["instructions"]
    
    await db_session.refresh(test_recipe)
    assert test_recipe.meal_name == update_data["meal_name"]
    assert json.loads(test_recipe.ingredients) == update_data["ingredients"]
    assert json.loads(test_recipe.instructions) == update_data["instructions"]


@pytest.mark.asyncio
async def test_update_recipe_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test updating a non-existent recipe."""
    nonexistent_recipe_id = 9999
    update_data = {
        "meal_name": "This will not be updated"
    }
    
    response = await async_client.patch(
        f"/recipe/{nonexistent_recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_recipe_unauthorized(
    async_client: AsyncClient,
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe without authorization."""
    recipe_id = test_recipe.id
    update_data = {
        "meal_name": "Unauthorized Update"
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_recipe_empty_payload(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe with an empty payload."""
    recipe_id = test_recipe.id
    empty_data: dict[str, object] = {}
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=empty_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["meal_name"] == test_recipe.meal_name
    assert data["meal_type"] == test_recipe.meal_type


@pytest.mark.asyncio
async def test_update_recipe_invalid_meal_type(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe with an invalid meal type."""
    recipe_id = test_recipe.id
    update_data = {
        "meal_type": "invalid_type"  # Invalid meal type
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    errors = response_data["detail"]
    assert any(error["loc"][1] == "meal_type" for error in errors)


@pytest.mark.asyncio
async def test_update_recipe_empty_ingredient(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe with an empty ingredient."""
    recipe_id = test_recipe.id
    update_data = {
        "ingredients": ["Valid ingredient", ""]  # Empty ingredient
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    errors = response_data["detail"]
    assert any(error["loc"][1] == "ingredients" for error in errors)


@pytest.mark.asyncio
async def test_update_other_users_recipe(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    other_user_recipe: TestRecipe
) -> None:
    """Test updating a recipe owned by another user."""
    recipe_id = other_user_recipe.id
    update_data = {
        "meal_name": "Trying to Update Someone Else's Recipe"
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Recipe not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_recipe_empty_ingredients(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe with an empty ingredients list."""
    recipe_id = test_recipe.id
    update_data: dict[str, list[str]] = {
        "ingredients": []
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["ingredients"] == []


@pytest.mark.asyncio
async def test_update_recipe_invalid_ingredients(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test updating a recipe with invalid ingredients (empty string)."""
    recipe_id = test_recipe.id
    update_data = {
        "ingredients": ["Valid ingredient", ""]  # Empty string is invalid
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "Input should be a valid string" in str(data["detail"])


@pytest.mark.asyncio
async def test_update_recipe_validation_error_handling(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe: TestRecipe
) -> None:
    """Test update validation error handling."""
    recipe_id = test_recipe.id
    
    invalid_update_data = {
        "meal_type": "invalid_meal_type"
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=invalid_update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    
    invalid_ingredients_data = {
        "ingredients": ["", None]
    }
    
    response = await async_client.patch(
        f"/recipe/{recipe_id}",
        json=invalid_ingredients_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY