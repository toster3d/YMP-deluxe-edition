from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status

from src.resources.plan_resource import ChooseMealResource, ScheduleResource


class TestScheduleResource:
    """Test suite for ScheduleResource."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Fixture providing a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def schedule_resource(self, mock_db: AsyncMock) -> ScheduleResource:
        """Fixture providing a ScheduleResource instance with mocked dependencies."""
        resource = ScheduleResource(mock_db)
        resource.user_plan_manager = AsyncMock()
        return resource

    @pytest.fixture
    def test_date(self) -> date:
        """Fixture providing a test date."""
        return date(2023, 11, 15)

    @pytest.fixture
    def test_user_id(self) -> int:
        """Fixture providing a test user ID."""
        return 1

    @pytest.mark.asyncio
    async def test_get_with_empty_plans(
        self, schedule_resource: ScheduleResource, test_user_id: int, test_date: date
    ) -> None:
        """Test retrieving schedule when user_plan_manager.get_plans returns an empty dictionary."""
        with patch.object(schedule_resource.user_plan_manager, 'get_plans', return_value={}):
            result = await schedule_resource.get(test_user_id, test_date)
            
            assert result["date"] == test_date.isoformat()
            assert result["user_plans"]["user_id"] == test_user_id
            assert result["user_plans"]["breakfast"] is None
            assert result["user_plans"]["lunch"] is None
            assert result["user_plans"]["dinner"] is None
            assert result["user_plans"]["dessert"] is None

    @pytest.mark.asyncio
    async def test_get_with_partial_plans(
        self, schedule_resource: ScheduleResource, test_user_id: int, test_date: date
    ) -> None:
        """Test retrieving schedule with partial data (only lunch and dinner)."""
        partial_plans = {
            "lunch": "Chicken Salad",
            "dinner": "Salmon with Vegetables"
        }
        
        with patch.object(schedule_resource.user_plan_manager, 'get_plans', return_value=partial_plans):
            result = await schedule_resource.get(test_user_id, test_date)
            
            assert result["date"] == test_date.isoformat()
            assert result["user_plans"]["user_id"] == test_user_id
            assert result["user_plans"]["breakfast"] is None
            assert result["user_plans"]["lunch"] == "Chicken Salad"
            assert result["user_plans"]["dinner"] == "Salmon with Vegetables"
            assert result["user_plans"]["dessert"] is None

    @pytest.mark.asyncio
    async def test_get_with_full_plans(
        self, schedule_resource: ScheduleResource, test_user_id: int, test_date: date
    ) -> None:
        """Test retrieving schedule with all meal types filled."""
        full_plans = {
            "breakfast": "Oatmeal with Berries",
            "lunch": "Chicken Salad",
            "dinner": "Salmon with Vegetables",
            "dessert": "Chocolate Cake"
        }
        
        with patch.object(schedule_resource.user_plan_manager, 'get_plans', return_value=full_plans):
            result = await schedule_resource.get(test_user_id, test_date)
            
            assert result["date"] == test_date.isoformat()
            assert result["user_plans"]["user_id"] == test_user_id
            assert result["user_plans"]["breakfast"] == "Oatmeal with Berries"
            assert result["user_plans"]["lunch"] == "Chicken Salad"
            assert result["user_plans"]["dinner"] == "Salmon with Vegetables"
            assert result["user_plans"]["dessert"] == "Chocolate Cake"

    @pytest.mark.asyncio
    async def test_get_without_date_parameter(
        self, schedule_resource: ScheduleResource, test_user_id: int
    ) -> None:
        """Test retrieving schedule without providing a date parameter."""
        from datetime import date as date_type
        
        today = date_type.today()
        breakfast_plan = {"breakfast": "Oatmeal with Berries"}
        
        with patch.object(schedule_resource.user_plan_manager, 'get_plans', return_value=breakfast_plan):
            result = await schedule_resource.get(test_user_id)
            
            assert result["date"] == today.isoformat()
            assert result["user_plans"]["user_id"] == test_user_id
            assert result["user_plans"]["breakfast"] == "Oatmeal with Berries"

    @pytest.mark.asyncio
    async def test_get_with_invalid_date_format(
        self, schedule_resource: ScheduleResource, test_user_id: int
    ) -> None:
        """Test handling invalid date format."""
        with patch.object(schedule_resource.user_plan_manager, 'get_plans', side_effect=ValueError("Invalid date format")):
            with pytest.raises(HTTPException) as exc_info:
                await schedule_resource.get(test_user_id, "invalid-date")  # type: ignore[arg-type]
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid date format" in str(exc_info.value.detail)


class TestChooseMealResource:
    """Test suite for ChooseMealResource."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Fixture providing a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def choose_meal_resource(self, mock_db: AsyncMock) -> ChooseMealResource:
        """Fixture providing a ChooseMealResource instance with mocked dependencies."""
        resource = ChooseMealResource(mock_db)
        resource.user_plan_manager = AsyncMock()
        return resource

    @pytest.fixture
    def test_user_id(self) -> int:
        """Fixture providing a test user ID."""
        return 1

    @pytest.fixture
    def test_date(self) -> date:
        """Fixture providing a test date."""
        return date(2023, 11, 15)

    @pytest.fixture
    def test_plan_data(self, test_date: date) -> AsyncMock:
        """Fixture providing test plan data."""
        plan_data = AsyncMock()
        plan_data.selected_date = test_date
        plan_data.recipe_id = 42
        plan_data.meal_type = "dinner"
        return plan_data

    @pytest.mark.asyncio
    async def test_get_empty_recipes(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int
    ) -> None:
        """Test retrieving recipes when user_plan_manager.get_user_recipes returns an empty list."""
        with patch.object(choose_meal_resource.user_plan_manager, 'get_user_recipes', return_value=[]):
            result = await choose_meal_resource.get(test_user_id)
            
            assert "recipes" in result
            assert isinstance(result["recipes"], list)
            assert len(result["recipes"]) == 0

    @pytest.mark.asyncio
    async def test_get_with_recipes(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int
    ) -> None:
        """Test retrieving recipes when user_plan_manager.get_user_recipes returns a list of recipes."""
        test_recipes = [
            {"id": 1, "name": "Recipe 1"},
            {"id": 2, "name": "Recipe 2"}
        ]
        
        with patch.object(choose_meal_resource.user_plan_manager, 'get_user_recipes', return_value=test_recipes):
            result = await choose_meal_resource.get(test_user_id)
            
            assert "recipes" in result
            assert result["recipes"] == test_recipes

    @pytest.mark.asyncio
    async def test_post_success(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int, test_plan_data: AsyncMock
    ) -> None:
        """Test successful meal plan update."""
        expected_result = {"message": "Meal plan updated successfully!", "id": 1}
        
        with patch.object(choose_meal_resource.user_plan_manager, 'create_or_update_plan', return_value=expected_result):
            result = await choose_meal_resource.post(test_user_id, test_plan_data)
            
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_post_with_validation_error(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int, test_plan_data: AsyncMock
    ) -> None:
        """Test handling validation error in post method."""
        with patch.object(choose_meal_resource.user_plan_manager, 'create_or_update_plan', side_effect=ValueError("Invalid meal type")):
            with pytest.raises(HTTPException) as exc_info:
                await choose_meal_resource.post(test_user_id, test_plan_data)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid meal type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_post_with_unexpected_exception(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int, test_plan_data: AsyncMock
    ) -> None:
        """Test handling unexpected exception in post method."""
        with patch.object(choose_meal_resource.user_plan_manager, 'create_or_update_plan', side_effect=Exception("Database error")):
            with pytest.raises(HTTPException) as exc_info:
                await choose_meal_resource.post(test_user_id, test_plan_data)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "An error occurred while updating the meal plan" in str(exc_info.value.detail)
            assert "Database error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_post_with_different_meal_types(
        self, choose_meal_resource: ChooseMealResource, test_user_id: int, test_date: date
    ) -> None:
        """Test updating different meal types."""
        meal_types = ["breakfast", "lunch", "dinner", "dessert"]
        expected_result = {"message": "Meal plan updated successfully!", "id": 1}
        
        with patch.object(choose_meal_resource.user_plan_manager, 'create_or_update_plan', return_value=expected_result):
            for meal_type in meal_types:
                plan_data = AsyncMock()
                plan_data.selected_date = test_date
                plan_data.recipe_id = 42
                plan_data.meal_type = meal_type
                
                result = await choose_meal_resource.post(test_user_id, plan_data)
                
                assert result == expected_result 