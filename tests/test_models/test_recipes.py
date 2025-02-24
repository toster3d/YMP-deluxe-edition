import uuid
from datetime import date
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from resources.pydantic_schemas import VALID_MEAL_TYPES
from test_models.models_db_test import TestRecipe, TestUser, TestUserPlan

# Konfiguracja testowej bazy danych
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def unique_user(test_db_session: AsyncSession) -> TestUser:
    """Fixture tworząca unikalnego użytkownika."""
    user = TestUser(
        user_name=f"TestUser-{uuid.uuid4()}",
        hash="hashedpassword",
        email=f"test{uuid.uuid4()}@example.com"
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user

@pytest.mark.anyio
async def test_create_recipe(test_db_session: AsyncSession, unique_user: TestUser) -> None:
    """Testuje dodanie przepisu i powiązanie z użytkownikiem."""
    recipe = TestRecipe(
        user_id=unique_user.id,
        meal_name="Spaghetti Bolognese",
        meal_type=VALID_MEAL_TYPES[2],
        ingredients="Makaron, mięso mielone, pomidory",
        instructions="Ugotować makaron, podsmażyć mięso, dodać pomidory"
    )
    test_db_session.add(recipe)
    await test_db_session.commit()
    await test_db_session.refresh(recipe)

    recipe_from_db = await test_db_session.get(
        TestRecipe, recipe.id, options=[selectinload(TestRecipe.user)]
    )

    # Rozszerzone asercje
    assert recipe_from_db is not None, "Przepis nie został poprawnie zapisany w bazie danych"
    assert recipe_from_db.id is not None, "ID przepisu nie może być None"
    assert recipe_from_db.meal_name == "Spaghetti Bolognese", "Nazwa posiłku nie zgadza się"
    assert recipe_from_db.meal_type == VALID_MEAL_TYPES[2], "Typ posiłku nie zgadza się"
    assert recipe_from_db.ingredients == "Makaron, mięso mielone, pomidory", "Składniki nie zgadzają się"
    assert recipe_from_db.instructions == "Ugotować makaron, podsmażyć mięso, dodać pomidory", "Instrukcje nie zgadzają się"
    
    # Sprawdzenie relacji użytkownika
    assert recipe_from_db.user is not None, "Użytkownik nie został poprawnie powiązany z przepisem"
    assert recipe_from_db.user.id == unique_user.id, "ID użytkownika nie zgadza się"

@pytest.mark.anyio
async def test_create_user(test_db_session: AsyncSession, unique_user: TestUser) -> None:
    """Testuje tworzenie użytkownika w bazie."""
    assert unique_user.id is not None
    assert "TestUser-" in unique_user.user_name
    assert "test" in unique_user.email

def test_user_has_recipes() -> None:
    """Sprawdza, czy użytkownik ma przypisane przepisy."""
    user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
    recipe1 = TestRecipe(user_id=user.id, meal_name="Pizza", meal_type="Dinner", ingredients="Ciasto, ser, sos", instructions="Upiec pizzę")
    recipe2 = TestRecipe(user_id=user.id, meal_name="Tiramisu", meal_type="Dessert", ingredients="Mascarpone, kawa, biszkopty", instructions="Wymieszać składniki")

    user.recipes = [recipe1, recipe2]

    assert user is not None
    assert len(user.recipes) == 2
    assert {r.meal_name for r in user.recipes} == {"Pizza", "Tiramisu"}

@pytest.mark.anyio
async def test_create_user_plan(test_db_session: AsyncSession, unique_user: TestUser) -> None:
    """Testuje dodanie planu użytkownika."""
    user_plan = TestUserPlan(
        user_id=unique_user.id,
        date=date(2025, 2, 20),
        breakfast="Jajecznica",
        lunch="Kurczak z ryżem",
        dinner="Kanapka",
        dessert="Czekolada"
    )
    test_db_session.add(user_plan)
    await test_db_session.commit()
    await test_db_session.refresh(user_plan)

    assert user_plan.id is not None
    assert user_plan.user_id == unique_user.id
    assert user_plan.breakfast == "Jajecznica"
