from datetime import date, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestUser, TestUserPlan


@pytest.fixture
async def user_with_meal_plan(db_session: AsyncSession, create_test_user: TestUser) -> tuple[TestUser, date, TestUserPlan]:
    """Fixture creating a user with meal plans for today and tomorrow."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    today_plan = TestUserPlan(
        user_id=create_test_user.id,
        date=today,
        breakfast="Scrambled eggs",
        lunch="Tomato soup",
        dinner="Spaghetti Bolognese",
        dessert="Tiramisu"
    )
    
    tomorrow_plan = TestUserPlan(
        user_id=create_test_user.id,
        date=tomorrow,
        breakfast="Oatmeal",
        lunch="Caesar salad",
        dinner="Salmon with vegetables",
        dessert=None  # No dessert
    )
    
    db_session.add_all([today_plan, tomorrow_plan])
    await db_session.commit()
    await db_session.refresh(today_plan)
    await db_session.refresh(tomorrow_plan)
    
    return create_test_user, today, today_plan


@pytest.mark.anyio
async def test_get_schedule_today(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    user_with_meal_plan: tuple[TestUser, date, TestUserPlan]
) -> None:
    """Test getting meal plan for today (default behavior)."""
    user, today, plan = user_with_meal_plan
    
    response = await async_client.get("/schedule", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["date"] == today.isoformat()
    assert data["user_plans"]["user_id"] == user.id
    assert data["user_plans"]["breakfast"] == plan.breakfast
    assert data["user_plans"]["lunch"] == plan.lunch
    assert data["user_plans"]["dinner"] == plan.dinner
    assert data["user_plans"]["dessert"] == plan.dessert


@pytest.mark.anyio
async def test_get_schedule_specific_date(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    user_with_meal_plan: tuple[TestUser, date, TestUserPlan]
) -> None:
    """Test getting meal plan for a specific date."""
    user, today, _ = user_with_meal_plan
    tomorrow = today + timedelta(days=1)
    
    response = await async_client.get(
        f"/schedule?date={tomorrow.isoformat()}", 
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["date"] == tomorrow.isoformat()
    assert data["user_plans"]["user_id"] == user.id
    assert data["user_plans"]["breakfast"] == "Oatmeal"
    assert data["user_plans"]["lunch"] == "Caesar salad"
    assert data["user_plans"]["dinner"] == "Salmon with vegetables"
    assert data["user_plans"]["dessert"] is None


@pytest.mark.anyio
async def test_get_schedule_nonexistent_date(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    user_with_meal_plan: tuple[TestUser, date, TestUserPlan]
) -> None:
    """Test getting meal plan for a date with no plan."""
    user, today, _ = user_with_meal_plan
    future_date = today + timedelta(days=30)
    
    response = await async_client.get(
        f"/schedule?date={future_date.isoformat()}", 
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["date"] == future_date.isoformat()
    assert data["user_plans"]["user_id"] == user.id
    assert data["user_plans"]["breakfast"] is None
    assert data["user_plans"]["lunch"] is None
    assert data["user_plans"]["dinner"] is None
    assert data["user_plans"]["dessert"] is None


@pytest.mark.anyio
async def test_get_schedule_invalid_date_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test response to invalid date format."""
    invalid_date = "28-02-2025"  # Invalid format, should be YYYY-MM-DD
    
    response = await async_client.get(
        f"/schedule?date={invalid_date}", 
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Invalid date format" in data["detail"]


@pytest.mark.anyio
async def test_get_schedule_unauthorized(
    async_client: AsyncClient
) -> None:
    """Test access attempt without authentication."""
    response = await async_client.get("/schedule")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.anyio
async def test_get_schedule_other_user_data(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession
) -> None:
    """Test that a user cannot see another user's plans."""
    other_user = TestUser(
        user_name="OtherUser",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    today = date.today()
    other_user_plan = TestUserPlan(
        user_id=other_user.id,
        date=today,
        breakfast="Cereal with milk",
        lunch="Dumplings",
        dinner="Potato pancakes",
        dessert="Cheesecake"
    )
    db_session.add(other_user_plan)
    await db_session.commit()
    
    response = await async_client.get("/schedule", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["user_plans"]["breakfast"] != "Cereal with milk"
    assert data["user_plans"]["lunch"] != "Dumplings"
    assert data["user_plans"]["dinner"] != "Potato pancakes"
    assert data["user_plans"]["dessert"] != "Cheesecake"


@pytest.mark.anyio
async def test_get_schedule_with_invalid_date_string(
    async_client: AsyncClient,
    auth_headers: dict[str, str]
) -> None:
    """Test handling of invalid date format in URL path."""
    response = await async_client.get(
        "/schedule?date=invalid-date",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Invalid date format" in data["detail"] 