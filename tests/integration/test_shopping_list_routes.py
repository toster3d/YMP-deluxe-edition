import json
from datetime import UTC, date, datetime, timedelta
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from test_models.models_db_test import TestRecipe, TestUserPlan

from helpers.date_range_generator import generate_date_list
from resources.pydantic_schemas import (
    VALID_MEAL_TYPES,
    ShoppingListRangeResponse,
    ShoppingListResponse,
)
from services.recipe_manager import RecipeManager
from services.shopping_list_service import ShoppingListService
from services.user_plan_manager import SqlAlchemyUserPlanManager


@pytest.fixture
async def setup_user_plan(db_session: AsyncSession, create_test_user: Any) -> AsyncGenerator[TestUserPlan, None]:
    """Create a test user plan for today."""
    today = datetime.now(UTC).date()
    
    user_plan = TestUserPlan(
        user_id=create_test_user.id,
        date=today,
        breakfast="Test Breakfast",
        lunch="Test Lunch",
        dinner="Test Dinner",
        dessert=None
    )
    
    db_session.add(user_plan)
    await db_session.commit()
    await db_session.refresh(user_plan)
    
    yield user_plan
    
    await db_session.delete(user_plan)
    await db_session.commit()


@pytest.fixture
async def setup_recipes(db_session: AsyncSession, create_test_user: Any) -> AsyncGenerator[list[TestRecipe], None]:
    """Create test recipes for the user."""
    recipes = []
    
    breakfast = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Breakfast",
        meal_type=VALID_MEAL_TYPES[0],
        ingredients=json.dumps(["eggs", "bread", "butter"]),
        instructions=json.dumps(["Cook eggs", "Toast bread", "Serve"])
    )
    
    lunch = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Lunch",
        meal_type=VALID_MEAL_TYPES[1],
        ingredients=json.dumps(["chicken", "rice", "vegetables"]),
        instructions=json.dumps(["Cook chicken", "Prepare rice", "Mix with vegetables"])
    )
    
    dinner = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Dinner",
        meal_type=VALID_MEAL_TYPES[2],
        ingredients=json.dumps(["pasta", "tomato sauce", "cheese"]),
        instructions=json.dumps(["Boil pasta", "Heat sauce", "Mix and add cheese"])
    )
    
    dessert = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Dessert",
        meal_type=VALID_MEAL_TYPES[3],
        ingredients=json.dumps(["flour", "sugar", "eggs", "chocolate"]),
        instructions=json.dumps(["Mix ingredients", "Bake", "Serve"])
    )
    
    recipes = [breakfast, lunch, dinner, dessert]
    db_session.add_all(recipes)
    await db_session.commit()
    
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    yield recipes
    
    for recipe in recipes:
        await db_session.delete(recipe)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_shopping_list_today(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    setup_user_plan: TestUserPlan,
    setup_recipes: list[TestRecipe]
) -> None:
    """Test getting shopping list for today."""
    response = await async_client.get("/shopping_list", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    data: dict[str, Any] = response.json()
    assert isinstance(data, dict)
    
    shopping_list: ShoppingListResponse = ShoppingListResponse(**data)
    assert shopping_list.current_date == datetime.now(UTC).date().isoformat()
    
    expected_ingredients = {"eggs", "bread", "butter", "chicken", "rice",
                            "vegetables", "pasta", "tomato sauce", "cheese"}
    assert set(shopping_list.ingredients) == expected_ingredients


@pytest.mark.asyncio
async def test_get_shopping_list_today_no_plan(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession
) -> None:
    """Test getting shopping list for today when no plan exists."""
    response = await async_client.get("/shopping_list", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No meal plan for today" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_shopping_list_date_range(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    setup_user_plan: TestUserPlan,
    setup_recipes: list[TestRecipe],
    db_session: AsyncSession,
    create_test_user: Any
) -> None:
    """Test getting shopping list for date range."""
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    tomorrow_plan = TestUserPlan(
        user_id=create_test_user.id,
        date=tomorrow,
        breakfast="Test Breakfast",
        lunch=None,
        dinner="Test Dinner",
        dessert="New Dessert"
    )
    
    db_session.add(tomorrow_plan)
    await db_session.commit()
    
    dessert = TestRecipe(
        user_id=create_test_user.id,
        meal_name="New Dessert",
        meal_type=VALID_MEAL_TYPES[3],
        ingredients=json.dumps(["flour", "sugar", "chocolate"]),
        instructions=json.dumps(["Mix ingredients", "Bake", "Serve"])
    )
    
    db_session.add(dessert)
    await db_session.commit()
    
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": tomorrow.isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    data: dict[str, Any] = response.json()
    assert isinstance(data, dict)
    
    shopping_list: ShoppingListRangeResponse = ShoppingListRangeResponse(**data)
    assert shopping_list.date_range == f"{today.isoformat()} to {tomorrow.isoformat()}"
    
    expected_ingredients = {
        "eggs", "bread", "butter",
        "chicken", "rice", "vegetables",
        "pasta", "tomato sauce", "cheese",
        "flour", "sugar", "chocolate"
    }
    assert set(shopping_list.ingredients) == expected_ingredients
    
    await db_session.delete(tomorrow_plan)
    await db_session.delete(dessert)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_no_plan(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test getting shopping list for date range when no plan exists."""
    today = datetime.now(UTC).date()
    next_week = today + timedelta(days=7)
    
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": next_week.isoformat(),
            "end_date": (next_week + timedelta(days=2)).isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No meal plan for this date range" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_invalid_dates(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test getting shopping list with end date before start date."""
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": yesterday.isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No meal plan for this date range" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_missing_body(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test POST shopping list endpoint with missing body."""
    response = await async_client.post("/shopping_list", headers=auth_headers)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "body" in response.json()["detail"][0]["loc"]


@pytest.mark.asyncio
async def test_get_shopping_list_unauthorized(async_client: AsyncClient) -> None:
    """Test accessing shopping list without authentication."""
    response = await async_client.get("/shopping_list")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_unauthorized(async_client: AsyncClient) -> None:
    """Test accessing shopping list date range without authentication."""
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": tomorrow.isoformat()
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
async def setup_test_data(
    db_session: AsyncSession, create_test_user: Any
) -> AsyncGenerator[tuple[list[TestUserPlan], list[TestRecipe]], None]:
    """Set up test data for shopping list service tests."""
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    plans = [
        TestUserPlan(
            user_id=create_test_user.id,
            date=today,
            breakfast="Oatmeal",
            lunch="Chicken Salad",
            dinner="Pasta",
            dessert=None
        ),
        TestUserPlan(
            user_id=create_test_user.id,
            date=tomorrow,
            breakfast="Pancakes",
            lunch=None,
            dinner="Steak",
            dessert="Chocolate Cake"
        )
    ]
    
    recipes = [
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Oatmeal",
            meal_type="breakfast",
            ingredients=json.dumps(["oats", "milk", "honey"]),
            instructions=json.dumps(["Mix ingredients", "Cook"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Chicken Salad",
            meal_type="lunch",
            ingredients=json.dumps(["chicken", "lettuce", "tomatoes", "dressing"]),
            instructions=json.dumps(["Cook chicken", "Mix with vegetables"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Pasta",
            meal_type="dinner",
            ingredients=json.dumps(["pasta", "tomato sauce", "cheese"]),
            instructions=json.dumps(["Boil pasta", "Mix with sauce"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Pancakes",
            meal_type="breakfast",
            ingredients=json.dumps(["flour", "eggs", "milk", "sugar"]),
            instructions=json.dumps(["Mix ingredients", "Cook on pan"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Steak",
            meal_type="dinner",
            ingredients=json.dumps(["beef steak", "salt", "pepper", "butter"]),
            instructions=json.dumps(["Season steak", "Cook to desired doneness"])
        ),
        TestRecipe(
            user_id=create_test_user.id,
            meal_name="Chocolate Cake",
            meal_type="dessert",
            ingredients=json.dumps(["flour", "sugar", "cocoa powder", "eggs", "butter"]),
            instructions=json.dumps(["Mix ingredients", "Bake in oven"])
        )
    ]
    
    db_session.add_all(plans)
    db_session.add_all(recipes)
    await db_session.commit()
    
    for plan in plans:
        await db_session.refresh(plan)
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    yield plans, recipes
    
    for plan in plans:
        await db_session.delete(plan)
    for recipe in recipes:
        await db_session.delete(recipe)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_ingredients_for_date_range(
    db_session: AsyncSession, create_test_user: Any, setup_test_data: tuple[list[TestUserPlan], list[TestRecipe]]
) -> None:
    """Test getting ingredients for date range."""
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, tomorrow)
    )
    
    expected_ingredients = {
        "oats", "milk", "honey",
        "chicken", "lettuce", "tomatoes", "dressing",
        "pasta", "tomato sauce", "cheese",
        "flour", "eggs", "sugar",
        "beef steak", "salt", "pepper", "butter",
        "cocoa powder"
    }
    
    assert ingredients == expected_ingredients


@pytest.mark.asyncio
async def test_get_ingredients_for_single_date(
    db_session: AsyncSession, create_test_user: Any, setup_test_data: tuple[list[TestUserPlan], list[TestRecipe]]
) -> None:
    """Test getting ingredients for a single date."""
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, today)
    )
    
    expected_ingredients = {
        "oats", "milk", "honey",
        "chicken", "lettuce", "tomatoes", "dressing",
        "pasta", "tomato sauce", "cheese",
    }
    
    assert ingredients == expected_ingredients


@pytest.mark.asyncio
async def test_get_ingredients_no_plans(
    db_session: AsyncSession, create_test_user: Any
) -> None:
    """Test getting ingredients when no plans exist."""
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    next_week = today + timedelta(days=7)
    
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (next_week, next_week + timedelta(days=2))
    )
    
    assert ingredients == set()


@pytest.mark.asyncio
async def test_get_ingredients_no_recipes(
    db_session: AsyncSession, create_test_user: Any
) -> None:
    """Test getting ingredients when plans exist but no recipes."""
    today = datetime.now(UTC).date()
    
    plan = TestUserPlan(
        user_id=create_test_user.id,
        date=today,
        breakfast="Missing Recipe",
        lunch=None,
        dinner="Another Missing Recipe",
        dessert=None
    )
    
    db_session.add(plan)
    await db_session.commit()
    
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, today)
    )
    
    assert ingredients == set()
    
    await db_session.delete(plan)
    await db_session.commit()


@pytest.mark.asyncio
async def test_extract_meal_name() -> None:
    """Test the _extract_meal_name method."""
    user_plan_manager: AsyncMock = AsyncMock()
    recipe_manager: AsyncMock = AsyncMock()
    service: ShoppingListService = ShoppingListService(user_plan_manager, recipe_manager)
    
    test_cases = [
        ("Pasta (ID: 123)", "Pasta"),
        ("Chicken Salad - Lunch", "Chicken Salad"),
        ("Simple Meal", "Simple Meal"),
        ("", None),
        ("None", None),
        ("null", None),
        (None, None)
    ]
    
    for input_value, expected_output in test_cases:
        if input_value is not None:
            result: str | None = service.extract_meal_name(input_value or "None")
            assert result == expected_output
async def test_get_meal_names() -> None:
    """Test the _get_meal_names method."""
    user_plan_manager = AsyncMock()
    recipe_manager = AsyncMock()
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    user_plan = {
        "breakfast": "Oatmeal (ID: 1)",
        "lunch": "Chicken Salad - Lunch",
        "dinner": "Pasta",
        "dessert": None
    }
    
    meal_names = list(service.get_meal_names(user_plan))
    
    assert meal_names == ["Oatmeal", "Chicken Salad", "Pasta"]


@pytest.mark.asyncio
async def test_safe_get_ingredients() -> None:
    """Test the _safe_get_ingredients method."""
    user_plan_manager = AsyncMock()
    recipe_manager = AsyncMock()
    recipe_manager.get_ingredients_by_meal_name.side_effect = [
        ["ingredient1", "ingredient2"],
        [],
        Exception("Recipe not found")
    ]
    
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    result1 = await service.safe_get_ingredients(1, "Meal1")
    assert result1 == ["ingredient1", "ingredient2"]
    
    result2 = await service.safe_get_ingredients(1, "Meal2")
    assert result2 == []
    
    result3 = await service.safe_get_ingredients(1, "Meal3")
    assert result3 == []


def test_generate_date_list() -> None:
    """Test the generate_date_list helper function."""
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 5)
    
    date_list = generate_date_list(start_date, end_date)
    
    expected_dates = [
        date(2023, 1, 1),
        date(2023, 1, 2),
        date(2023, 1, 3),
        date(2023, 1, 4),
        date(2023, 1, 5)
    ]
    assert date_list == expected_dates
    
    single_day = generate_date_list(start_date, start_date)
    assert single_day == [start_date] 