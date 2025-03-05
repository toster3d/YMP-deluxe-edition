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
    """Utwórz przepis testowy do usunięcia."""
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
    """Utwórz przepis należący do innego użytkownika."""
    # Utwórz innego użytkownika
    other_user = TestUser(
        user_name="OtherUser",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Utwórz przepis dla tego użytkownika
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
async def test_delete_recipe_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_recipe_for_deletion: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test pomyślnego usunięcia przepisu."""
    # Arrange
    recipe_id = test_recipe_for_deletion.id
    
    # Act
    response = await async_client.delete(
        f"/recipe/{recipe_id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Sprawdź, czy przepis został usunięty z bazy danych
    query = select(TestRecipe).filter_by(id=recipe_id)
    result = await db_session.execute(query)
    recipe = result.scalar_one_or_none()
    assert recipe is None


@pytest.mark.asyncio
async def test_delete_nonexistent_recipe(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test próby usunięcia nieistniejącego przepisu."""
    # Arrange
    nonexistent_recipe_id = 9999  # ID, które na pewno nie istnieje
    
    # Act
    response = await async_client.delete(
        f"/recipe/{nonexistent_recipe_id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Recipe not found"


@pytest.mark.asyncio
async def test_delete_recipe_unauthorized(
    async_client: AsyncClient,
    test_recipe_for_deletion: TestRecipe
) -> None:
    """Test próby usunięcia przepisu bez autoryzacji."""
    # Arrange
    recipe_id = test_recipe_for_deletion.id
    
    # Act
    response = await async_client.delete(
        f"/recipe/{recipe_id}"
        # Brak nagłówków autoryzacji
    )
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_data = response.json()
    assert "detail" in response_data


@pytest.mark.asyncio
async def test_delete_other_users_recipe(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    another_user_recipe: TestRecipe,
    db_session: AsyncSession
) -> None:
    """Test próby usunięcia przepisu należącego do innego użytkownika."""
    # Arrange
    recipe_id = another_user_recipe.id
    
    # Act
    response = await async_client.delete(
        f"/recipe/{recipe_id}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Recipe not found"
    
    # Sprawdź, czy przepis nadal istnieje w bazie danych
    query = select(TestRecipe).filter_by(id=recipe_id)
    result = await db_session.execute(query)
    recipe = result.scalar_one_or_none()
    assert recipe is not None


@pytest.mark.asyncio
async def test_delete_recipe_invalid_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test próby usunięcia przepisu z nieprawidłowym ID."""
    # Act
    response = await async_client.delete(
        "/recipe/invalid_id",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data 