from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.resources.plan_resource import ChooseMealResource, ScheduleResource


@pytest.mark.asyncio
async def test_schedule_resource_get_with_empty_plans() -> None:
    """Test retrieving schedule when user_plan_manager.get_plans returns an empty dictionary."""
    mock_db = AsyncMock()
    schedule_resource = ScheduleResource(mock_db)
    
    mock_plan_manager = AsyncMock()
    mock_plan_manager.get_plans.return_value = {}
    schedule_resource.user_plan_manager = mock_plan_manager
    
    user_id = 1
    test_date = date(2023, 11, 15)
    
    result = await schedule_resource.get(user_id, test_date)
    
    assert result["date"] == test_date.isoformat()
    assert result["user_plans"]["user_id"] == user_id
    assert result["user_plans"]["breakfast"] is None
    assert result["user_plans"]["lunch"] is None
    assert result["user_plans"]["dinner"] is None
    assert result["user_plans"]["dessert"] is None
    
    mock_plan_manager.get_plans.assert_awaited_once_with(user_id, test_date)


@pytest.mark.asyncio
async def test_schedule_resource_get_with_partial_plans() -> None:
    """Test retrieving schedule with partial data (only lunch and dinner)."""
    mock_db = AsyncMock()
    schedule_resource = ScheduleResource(mock_db)
    
    mock_plan_manager = AsyncMock()
    mock_plan_manager.get_plans.return_value = {
        "lunch": "Chicken Salad",
        "dinner": "Salmon with Vegetables"
    }
    schedule_resource.user_plan_manager = mock_plan_manager
    
    user_id = 1
    test_date = date(2023, 11, 15)
    
    result = await schedule_resource.get(user_id, test_date)
    
    assert result["date"] == test_date.isoformat()
    assert result["user_plans"]["user_id"] == user_id
    assert result["user_plans"]["breakfast"] is None
    assert result["user_plans"]["lunch"] == "Chicken Salad"
    assert result["user_plans"]["dinner"] == "Salmon with Vegetables"
    assert result["user_plans"]["dessert"] is None

@pytest.mark.asyncio
async def test_choose_meal_resource_get_empty_recipes() -> None:
    """Test retrieving recipes when user_plan_manager.get_user_recipes returns an empty list."""
    mock_db = AsyncMock()
    choose_meal_resource = ChooseMealResource(mock_db)
    
    mock_plan_manager = AsyncMock()
    mock_plan_manager.get_user_recipes.return_value = []
    choose_meal_resource.user_plan_manager = mock_plan_manager
    
    user_id = 1
    
    result = await choose_meal_resource.get(user_id)
    
    assert "recipes" in result
    assert isinstance(result["recipes"], list)
    assert len(result["recipes"]) == 0
    
    mock_plan_manager.get_user_recipes.assert_awaited_once_with(user_id)

@pytest.mark.asyncio
async def test_choose_meal_resource_post_with_unexpected_exception() -> None:
    """Test handling unexpected exception in post method."""
    mock_db = AsyncMock()
    choose_meal_resource = ChooseMealResource(mock_db)
    
    mock_plan_manager = AsyncMock()
    mock_plan_manager.create_or_update_plan.side_effect = Exception("Database error")
    choose_meal_resource.user_plan_manager = mock_plan_manager
    
    user_id = 1
    plan_data = AsyncMock()
    plan_data.selected_date = date(2023, 11, 15)
    plan_data.recipe_id = 42
    plan_data.meal_type = "dinner"
    
    with pytest.raises(HTTPException) as exc_info:
        await choose_meal_resource.post(user_id, plan_data)
    
    assert exc_info.value.status_code == 500
    assert "An error occurred while updating the meal plan" in str(exc_info.value.detail)
    assert "Database error" in str(exc_info.value.detail) 