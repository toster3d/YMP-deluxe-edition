import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from resources.pydantic_schemas import VALID_MEAL_TYPES
from test_models.models_db_test import TestRecipe, TestUser, TestUserPlan


@pytest.fixture
async def unique_user(db_session: AsyncSession) -> TestUser:
    """Fixture creating a unique user."""
    user = TestUser(
        user_name=f"TestUser-{uuid.uuid4()}",
        hash="hashedpassword",
        email=f"test{uuid.uuid4()}@example.com"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.mark.anyio
async def test_create_recipe(db_session: AsyncSession, unique_user: TestUser) -> None:
    """Tests adding a recipe and linking it to a user."""
    recipe = TestRecipe(
        user_id=unique_user.id,
        meal_name="Test Meal",
        meal_type=VALID_MEAL_TYPES[0],
        ingredients="Test Ingredients",
        instructions="Test Instructions"
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    recipe_from_db = await db_session.get(
        TestRecipe, recipe.id, options=[selectinload(TestRecipe.user)]
    )

    assert recipe_from_db is not None
    assert recipe_from_db.user.id == unique_user.id

@pytest.mark.anyio
async def test_create_user(db_session: AsyncSession, unique_user: TestUser) -> None:
    """Tests creating a user in the database."""
    assert unique_user.id is not None
    assert "TestUser-" in unique_user.user_name
    assert "test" in unique_user.email

def test_user_has_recipes() -> None:
    """Checks if the user has assigned recipes."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    recipe1 = TestRecipe(user_id=user.id, meal_name="Pizza", meal_type="Dinner", ingredients="Dough, cheese, sauce", instructions="Bake the pizza")
    recipe2 = TestRecipe(user_id=user.id, meal_name="Tiramisu", meal_type="Dessert", ingredients="Mascarpone, coffee, ladyfingers", instructions="Mix the ingredients")

    user.recipes = [recipe1, recipe2]

    assert user is not None
    assert len(user.recipes) == 2
    assert {r.meal_name for r in user.recipes} == {"Pizza", "Tiramisu"}

@pytest.mark.anyio
async def test_create_user_plan(db_session: AsyncSession, unique_user: TestUser) -> None:
    """Tests adding a user plan."""
    user_plan = TestUserPlan(
        user_id=unique_user.id,
        date=date(2025, 2, 20),
        breakfast="Scrambled eggs",
        lunch="Chicken with rice",
        dinner="Sandwich",
        dessert="Chocolate"
    )
    db_session.add(user_plan)
    await db_session.commit()
    await db_session.refresh(user_plan)

    assert user_plan.id is not None
    assert user_plan.user_id == unique_user.id
    assert user_plan.breakfast == "Scrambled eggs"
