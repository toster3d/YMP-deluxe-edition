from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from resources.pydantic_schemas import VALID_MEAL_TYPES
from test_models.models_db_test import TestRecipe, TestUser, TestUserPlan


@pytest.mark.asyncio
async def test_create_recipe(db_session: AsyncSession) -> None:
    """Testuje dodanie przepisu i powiązanie z użytkownikiem."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    recipe = TestRecipe(
        user_id=user.id,
        meal_name="Spaghetti Bolognese",
        meal_type=VALID_MEAL_TYPES[2],  # Zakładając, że 'dinner' jest na pozycji 2
        ingredients="Makaron, mięso mielone, pomidory",
        instructions="Ugotować makaron, podsmażyć mięso, dodać pomidory"
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    assert recipe.id is not None
    assert recipe.meal_name == "Spaghetti Bolognese"
    assert recipe.meal_type in VALID_MEAL_TYPES
    assert recipe.user_id == user.id
    assert recipe.user == user


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Testuje tworzenie użytkownika w bazie."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.user_name == "TestUser"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_user_has_recipes(db_session: AsyncSession) -> None:
    """Sprawdza, czy użytkownik ma przypisane przepisy."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    recipe1 = TestRecipe(
        user_id=user.id, 
        meal_name="Pizza", 
        meal_type=VALID_MEAL_TYPES[2],  # 'dinner'
        ingredients="Ciasto, ser, sos", 
        instructions="Upiec pizzę"
    )
    recipe2 = TestRecipe(
        user_id=user.id, 
        meal_name="Tiramisu", 
        meal_type=VALID_MEAL_TYPES[3],  # 'dessert'
        ingredients="Mascarpone, kawa, biszkopty", 
        instructions="Wymieszać składniki"
    )

    db_session.add_all([recipe1, recipe2])
    await db_session.commit()

    user_from_db = await db_session.get(TestUser, user.id)
    assert user_from_db is not None
    assert len(user_from_db.recipes) == 2
    assert user_from_db.recipes[0].meal_name == "Pizza"
    assert user_from_db.recipes[1].meal_name == "Tiramisu"
    
@pytest.mark.asyncio
async def test_create_user_plan(db_session: AsyncSession) -> None:
    """Testuje dodanie planu użytkownika."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    user_plan = TestUserPlan(
        user_id=user.id,
        date=date(2025, 2, 20),
        breakfast="Jajecznica",
        lunch="Kurczak z ryżem",
        dinner="Kanapka",
        dessert="Czekolada"
    )
    db_session.add(user_plan)
    await db_session.commit()
    await db_session.refresh(user_plan)

    assert user_plan.id is not None
    assert user_plan.user_id == user.id
    assert user_plan.breakfast == "Jajecznica"
