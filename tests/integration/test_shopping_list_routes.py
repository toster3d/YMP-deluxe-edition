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
    
    # Create user plan for today
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
    
    # Cleanup
    await db_session.delete(user_plan)
    await db_session.commit()


@pytest.fixture
async def setup_recipes(db_session: AsyncSession, create_test_user: Any) -> AsyncGenerator[list[TestRecipe], None]:
    """Create test recipes for the user."""
    recipes = []
    
    # Create breakfast recipe
    breakfast = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Breakfast",
        meal_type=VALID_MEAL_TYPES[0],
        ingredients=json.dumps(["eggs", "bread", "butter"]),
        instructions=json.dumps(["Cook eggs", "Toast bread", "Serve"])
    )
    
    # Create lunch recipe
    lunch = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Lunch",
        meal_type=VALID_MEAL_TYPES[1],
        ingredients=json.dumps(["chicken", "rice", "vegetables"]),
        instructions=json.dumps(["Cook chicken", "Prepare rice", "Mix with vegetables"])
    )
    
    # Create dinner recipe
    dinner = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Dinner",
        meal_type=VALID_MEAL_TYPES[2],
        ingredients=json.dumps(["pasta", "tomato sauce", "cheese"]),
        instructions=json.dumps(["Boil pasta", "Heat sauce", "Mix and add cheese"])
    )
    
    # Create dessert recipe
    dessert = TestRecipe(
        user_id=create_test_user.id,
        meal_name="Test Dessert",
        meal_type=VALID_MEAL_TYPES[3],
        ingredients=json.dumps(["flour", "sugar", "eggs", "chocolate"]),
        instructions=json.dumps(["Mix ingredients", "Bake", "Serve"])
    )
    
    recipes.extend([breakfast, lunch, dinner, dessert])
    db_session.add_all(recipes)
    await db_session.commit()
    
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    yield recipes
    
    # Cleanup
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
    # Act
    response = await async_client.get("/shopping_list", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, dict)
    
    # Validate response structure
    shopping_list = ShoppingListResponse(**data)
    assert shopping_list.current_date == datetime.now(UTC).date().isoformat()
    
    # Check ingredients
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
    # Act
    response = await async_client.get("/shopping_list", headers=auth_headers)
    
    # Assert
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
    # Arrange
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    # Create plan for tomorrow
    tomorrow_plan = TestUserPlan(
        user_id=create_test_user.id,
        date=tomorrow,
        breakfast="Test Breakfast",  # Reuse same breakfast
        lunch=None,
        dinner="Test Dinner",  # Reuse same dinner
        dessert="New Dessert"  # New meal not in recipes
    )
    
    db_session.add(tomorrow_plan)
    await db_session.commit()
    
    # Create dessert recipe
    dessert = TestRecipe(
        user_id=create_test_user.id,
        meal_name="New Dessert",
        meal_type=MealType.dessert,
        ingredients=json.dumps(["flour", "sugar", "chocolate"]),
        instructions=json.dumps(["Mix ingredients", "Bake", "Serve"])
    )
    
    db_session.add(dessert)
    await db_session.commit()
    
    # Act
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": tomorrow.isoformat()
        },
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, dict)
    
    # Validate response structure
    shopping_list = ShoppingListRangeResponse(**data)
    assert shopping_list.date_range == f"{today.isoformat()} to {tomorrow.isoformat()}"
    
    # Check ingredients (should include all meals from both days)
    expected_ingredients = {
        "eggs", "bread", "butter",  # breakfast
        "chicken", "rice", "vegetables",  # lunch
        "pasta", "tomato sauce", "cheese",  # dinner
        "flour", "sugar", "chocolate"  # dessert
    }
    assert set(shopping_list.ingredients) == expected_ingredients
    
    # Cleanup
    await db_session.delete(tomorrow_plan)
    await db_session.delete(dessert)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_no_plan(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test getting shopping list for date range when no plan exists."""
    # Arrange
    today = datetime.now(UTC).date()
    next_week = today + timedelta(days=7)
    
    # Act
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": next_week.isoformat(),
            "end_date": (next_week + timedelta(days=2)).isoformat()
        },
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No meal plan for this date range" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_invalid_dates(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test getting shopping list with end date before start date."""
    # Arrange
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    
    # Act
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": yesterday.isoformat()
        },
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No meal plan for this date range" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_missing_body(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test POST shopping list endpoint with missing body."""
    # Act
    response = await async_client.post("/shopping_list", headers=auth_headers)
    
    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "body" in response.json()["detail"][0]["loc"]


@pytest.mark.asyncio
async def test_get_shopping_list_unauthorized(async_client: AsyncClient) -> None:
    """Test accessing shopping list without authentication."""
    # Act
    response = await async_client.get("/shopping_list")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_shopping_list_date_range_unauthorized(async_client: AsyncClient) -> None:
    """Test accessing shopping list date range without authentication."""
    # Arrange
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    # Act
    response = await async_client.post(
        "/shopping_list",
        json={
            "start_date": today.isoformat(),
            "end_date": tomorrow.isoformat()
        }
    )
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
async def setup_test_data(
    db_session: AsyncSession, create_test_user: Any
) -> AsyncGenerator[tuple[list[TestUserPlan], list[TestRecipe]], None]:
    """Set up test data for shopping list service tests."""
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    # Create user plans
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
    
    # Create recipes
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
    
    # Cleanup
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
    # Arrange
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    tomorrow = today + timedelta(days=1)
    
    # Act
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, tomorrow)
    )
    
    # Assert
    expected_ingredients = {
        "oats", "milk", "honey",  # Oatmeal
        "chicken", "lettuce", "tomatoes", "dressing",  # Chicken Salad
        "pasta", "tomato sauce", "cheese",  # Pasta
        "flour", "eggs", "sugar",  # Pancakes (milk is already included)
        "beef steak", "salt", "pepper", "butter",  # Steak
        "cocoa powder"  # Chocolate Cake (flour, sugar, eggs, butter already included)
    }
    
    assert ingredients == expected_ingredients


@pytest.mark.asyncio
async def test_get_ingredients_for_single_date(
    db_session: AsyncSession, create_test_user: Any, setup_test_data: tuple[list[TestUserPlan], list[TestRecipe]]
) -> None:
    """Test getting ingredients for a single date."""
    # Arrange
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    
    # Act
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, today)
    )
    
    # Assert
    expected_ingredients = {
        "oats", "milk", "honey",  # Oatmeal
        "chicken", "lettuce", "tomatoes", "dressing",  # Chicken Salad
        "pasta", "tomato sauce", "cheese",  # Pasta
    }
    
    assert ingredients == expected_ingredients


@pytest.mark.asyncio
async def test_get_ingredients_no_plans(
    db_session: AsyncSession, create_test_user: Any
) -> None:
    """Test getting ingredients when no plans exist."""
    # Arrange
    user_plan_manager = SqlAlchemyUserPlanManager(db_session)
    recipe_manager = RecipeManager(db_session)
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    today = datetime.now(UTC).date()
    next_week = today + timedelta(days=7)
    
    # Act
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (next_week, next_week + timedelta(days=2))
    )
    
    # Assert
    assert ingredients == set()


@pytest.mark.asyncio
async def test_get_ingredients_no_recipes(
    db_session: AsyncSession, create_test_user: Any
) -> None:
    """Test getting ingredients when plans exist but no recipes."""
    # Arrange
    today = datetime.now(UTC).date()
    
    # Create plan without corresponding recipes
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
    
    # Act
    ingredients = await service.get_ingredients_for_date_range(
        create_test_user.id, (today, today)
    )
    
    # Assert
    assert ingredients == set()
    
    # Cleanup
    await db_session.delete(plan)
    await db_session.commit()


@pytest.mark.asyncio
async def test_extract_meal_name() -> None:
    """Test the _extract_meal_name method."""
    # Arrange
    user_plan_manager = AsyncMock()
    recipe_manager = AsyncMock()
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    test_cases = [
        ("Pasta (ID: 123)", "Pasta"),
        ("Chicken Salad - Lunch", "Chicken Salad"),
        ("Simple Meal", "Simple Meal"),
        ("", None),
        ("None", None),
        ("null", None),
        (None, None)  # This will be converted to string in the actual method
    ]
    
    # Act & Assert
    for input_value, expected_output in test_cases:
        if input_value is not None:
            result = service._extract_meal_name(input_value)
        else:
            result = service._extract_meal_name("None")
        assert result == expected_output


@pytest.mark.asyncio
async def test_get_meal_names() -> None:
    """Test the _get_meal_names method."""
    # Arrange
    user_plan_manager = AsyncMock()
    recipe_manager = AsyncMock()
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    user_plan = {
        "breakfast": "Oatmeal (ID: 1)",
        "lunch": "Chicken Salad - Lunch",
        "dinner": "Pasta",
        "dessert": None
    }
    
    # Act
    meal_names = list(service._get_meal_names(user_plan))
    
    # Assert
    assert meal_names == ["Oatmeal", "Chicken Salad", "Pasta"]


@pytest.mark.asyncio
async def test_safe_get_ingredients() -> None:
    """Test the _safe_get_ingredients method."""
    # Arrange
    user_plan_manager = AsyncMock()
    recipe_manager = AsyncMock()
    recipe_manager.get_ingredients_by_meal_name.side_effect = [
        ["ingredient1", "ingredient2"],  # Normal case
        [],  # Empty ingredients
        Exception("Recipe not found")  # Exception case
    ]
    
    service = ShoppingListService(user_plan_manager, recipe_manager)
    
    # Act & Assert
    # Normal case
    result1 = await service._safe_get_ingredients(1, "Meal1")
    assert result1 == ["ingredient1", "ingredient2"]
    
    # Empty ingredients
    result2 = await service._safe_get_ingredients(1, "Meal2")
    assert result2 == []
    
    # Exception case
    result3 = await service._safe_get_ingredients(1, "Meal3")
    assert result3 == []


def test_generate_date_list() -> None:
    """Test the generate_date_list helper function."""
    # Arrange
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 5)
    
    # Act
    date_list = generate_date_list(start_date, end_date)
    
    # Assert
    expected_dates = [
        date(2023, 1, 1),
        date(2023, 1, 2),
        date(2023, 1, 3),
        date(2023, 1, 4),
        date(2023, 1, 5)
    ]
    assert date_list == expected_dates
    
    # Test single day
    single_day = generate_date_list(start_date, start_date)
    assert single_day == [start_date] 