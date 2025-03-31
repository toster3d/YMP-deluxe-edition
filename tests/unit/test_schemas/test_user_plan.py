"""Unit tests for UserPlanSchema, PlanSchema, and ScheduleResponse."""

import json
from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import (
    MealType,
    PlanSchema,
    ScheduleResponse,
    UserPlanSchema,
)


@pytest.mark.schema
class TestUserPlanSchema:
    """Test suite for UserPlanSchema validation and functionality."""

    @pytest.fixture
    def valid_plan_data(self) -> dict[str, Any]:
        """Fixture providing valid plan data."""
        return {
            "user_id": 1,
            "date": date(2024, 2, 14),
            "breakfast": "Pancakes",
            "lunch": "Salad",
            "dinner": "Steak",
            "dessert": "Ice Cream"
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_plan_data: dict[str, Any]) -> None:
            """Test valid UserPlanSchema creation."""
            plan = UserPlanSchema(**valid_plan_data)
            assert plan.user_id == 1
            assert plan.date == date(2024, 2, 14)
            assert plan.breakfast == "Pancakes"
            assert plan.lunch == "Salad"
            assert plan.dinner == "Steak"
            assert plan.dessert == "Ice Cream"

        def test_minimal(self) -> None:
            """Test UserPlanSchema with only required fields."""
            plan = UserPlanSchema(
                user_id=1,
                date=date(2024, 2, 14),
                breakfast=None,
                lunch=None,
                dinner=None,
                dessert=None
            )
            assert plan.user_id == 1
            assert plan.date == date(2024, 2, 14)
            assert plan.breakfast is None
            assert plan.lunch is None
            assert plan.dinner is None
            assert plan.dessert is None

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"date": "2024-02-14"}, "Field required"),
                ({"user_id": 1}, "Field required"),
                ({"user_id": "not_an_int", "date": "2024-02-14"}, "Input should be a valid integer"),
                ({"user_id": 1, "date": "invalid_date"}, "Input should be a valid date"),
            ],
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test UserPlanSchema validation."""
            with pytest.raises(ValidationError) as exc_info:
                UserPlanSchema(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestOptionalFields:
        """Tests for optional fields validation."""

        @pytest.mark.parametrize(
            "meal_type,meal_value",
            [
                ("breakfast", "Pancakes"),
                ("lunch", "Salad"),
                ("dinner", "Steak"),
                ("dessert", "Ice Cream"),
            ],
        )
        def test_individual_meals(self, meal_type: str, meal_value: str) -> None:
            """Test setting individual meals in UserPlanSchema."""
            data: dict[str, Any] = {
                "user_id": 1,
                "date": date(2024, 2, 14),
                meal_type: meal_value
            }
            plan = UserPlanSchema(**data)
            assert getattr(plan, meal_type) == meal_value

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"user_id": 1, "date": date(2024, 2, 14), "breakfast": 123}, "Input should be a valid string"),
                ({"user_id": 1, "date": date(2024, 2, 14), "lunch": 123}, "Input should be a valid string"),
                ({"user_id": 1, "date": date(2024, 2, 14), "dinner": 123}, "Input should be a valid string"),
                ({"user_id": 1, "date": date(2024, 2, 14), "dessert": 123}, "Input should be a valid string"),
            ],
        )
        def test_invalid_meal_types(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test validation of meal type values."""
            with pytest.raises(ValidationError) as exc_info:
                UserPlanSchema(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test UserPlanSchema model configuration."""
            schema = UserPlanSchema.model_json_schema()
            
            required = schema.get("required", [])
            assert "user_id" in required
            assert "date" in required
            
            properties = schema["properties"]
            assert properties["user_id"]["type"] == "integer"
            assert properties["date"]["type"] == "string"
            assert properties["date"]["format"] == "date"
            
            for meal in ["breakfast", "lunch", "dinner", "dessert"]:
                assert meal in properties
                assert "anyOf" in properties[meal]
                types = [t["type"] for t in properties[meal]["anyOf"]]
                assert "string" in types
                assert "null" in types

        def test_json_serialization(self, valid_plan_data: dict[str, Any]) -> None:
            """Test JSON serialization and deserialization."""
            plan = UserPlanSchema(**valid_plan_data)
            json_str = plan.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["user_id"] == 1
            assert data["date"] == "2024-02-14"
            assert data["breakfast"] == "Pancakes"
            assert data["lunch"] == "Salad"
            assert data["dinner"] == "Steak"
            assert data["dessert"] == "Ice Cream"

        def test_from_orm(self) -> None:
            """Test UserPlanSchema creation from ORM model."""
            from models.recipes import UserPlan
            
            orm_plan = UserPlan(
                id=1,
                user_id=1,
                date=date(2024, 2, 14),
                breakfast="Pancakes",
                lunch="Salad",
                dinner="Steak",
                dessert="Ice Cream"
            )
            
            plan = UserPlanSchema.model_validate(orm_plan)
            assert plan.user_id == 1
            assert plan.date == date(2024, 2, 14)
            assert plan.breakfast == "Pancakes"
            assert plan.lunch == "Salad"
            assert plan.dinner == "Steak"
            assert plan.dessert == "Ice Cream"


@pytest.mark.schema
class TestPlanSchema:
    """Test suite for PlanSchema validation and functionality."""

    @pytest.fixture
    def valid_plan_data(self) -> dict[str, Any]:
        """Fixture providing valid plan data."""
        return {
            "selected_date": date(2024, 2, 14),
            "recipe_id": 1,
            "meal_type": "breakfast"
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_plan_data: dict[str, Any]) -> None:
            """Test valid PlanSchema creation."""
            plan = PlanSchema(**valid_plan_data)
            assert plan.selected_date == date(2024, 2, 14)
            assert plan.recipe_id == 1
            assert plan.meal_type == "breakfast"

        @pytest.mark.parametrize(
            "meal_type",
            ["breakfast", "lunch", "dinner", "dessert"]
        )
        def test_valid_meal_types(self, meal_type: MealType, valid_plan_data: dict[str, Any]) -> None:
            """Test PlanSchema with all valid meal types."""
            valid_plan_data["meal_type"] = meal_type
            plan = PlanSchema(**valid_plan_data)
            assert plan.meal_type == meal_type

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"recipe_id": 1, "meal_type": "breakfast"}, "Field required"),
                ({"selected_date": "2024-02-14", "meal_type": "breakfast"}, "Field required"),
                ({"selected_date": "2024-02-14", "recipe_id": 1}, "Field required"),
                ({"selected_date": "invalid_date", "recipe_id": 1, "meal_type": "breakfast"}, "Input should be a valid date"),
                ({"selected_date": "2024-02-14", "recipe_id": "not_an_int", "meal_type": "breakfast"}, "Input should be a valid integer"),
                ({"selected_date": "2024-02-14", "recipe_id": 1, "meal_type": "invalid_meal_type"}, "Input should be 'breakfast', 'lunch', 'dinner' or 'dessert'"),
                ({"selected_date": "2024-02-14", "recipe_id": -1, "meal_type": "breakfast"}, "Input should be greater than 0"),
            ],
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test PlanSchema validation."""
            with pytest.raises(ValidationError) as exc_info:
                PlanSchema(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test PlanSchema model configuration."""
            schema = PlanSchema.model_json_schema()
            
            required = schema.get("required", [])
            assert "selected_date" in required
            assert "recipe_id" in required
            assert "meal_type" in required
            
            properties = schema["properties"]
            assert properties["selected_date"]["type"] == "string"
            assert properties["selected_date"]["format"] == "date"
            assert properties["recipe_id"]["type"] == "integer"
            assert properties["meal_type"]["type"] == "string"
            
            assert "description" in properties["selected_date"]
            assert "description" in properties["recipe_id"]
            assert "description" in properties["meal_type"]

        def test_json_serialization(self, valid_plan_data: dict[str, Any]) -> None:
            """Test that plan data can be properly serialized to JSON."""
            plan = PlanSchema(**valid_plan_data)
            json_str = plan.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["selected_date"] == "2024-02-14"
            assert data["recipe_id"] == 1
            assert data["meal_type"] == "breakfast"


@pytest.mark.schema
class TestScheduleResponse:
    """Test suite for ScheduleResponse validation and functionality."""

    @pytest.fixture
    def valid_schedule_data(self) -> dict[str, Any]:
        """Fixture providing valid schedule data."""
        return {
            "date": date(2024, 2, 14),
            "breakfast": "Pancakes",
            "lunch": "Salad",
            "dinner": "Steak",
            "dessert": "Ice Cream"
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_schedule_data: dict[str, Any]) -> None:
            """Test valid ScheduleResponse creation."""
            schedule = ScheduleResponse(**valid_schedule_data)
            assert schedule.date == date(2024, 2, 14)
            assert schedule.breakfast == "Pancakes"
            assert schedule.lunch == "Salad"
            assert schedule.dinner == "Steak"
            assert schedule.dessert == "Ice Cream"

        def test_minimal(self) -> None:
            """Test ScheduleResponse with only required fields."""
            schedule = ScheduleResponse(date=date(2024, 2, 14))
            assert schedule.date == date(2024, 2, 14)
            assert schedule.breakfast is None
            assert schedule.lunch is None
            assert schedule.dinner is None
            assert schedule.dessert is None

    class TestOptionalFields:
        """Tests for optional fields validation."""

        @pytest.mark.parametrize(
            "meal_type,meal_value",
            [
                ("breakfast", "Pancakes"),
                ("lunch", "Salad"),
                ("dinner", "Steak"),
                ("dessert", "Ice Cream"),
            ]
        )
        def test_individual_meals(self, meal_type: str, meal_value: str) -> None:
            """Test setting individual meals in ScheduleResponse."""
            data: dict[str, Any] = {
                "date": date(2024, 2, 14),
                meal_type: meal_value
            }
            schedule = ScheduleResponse(**data)
            assert getattr(schedule, meal_type) == meal_value

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({}, "Field required"),
                ({"date": "invalid_date"}, "Input should be a valid date"),
                ({"date": date(2024, 2, 14), "breakfast": 123}, "Input should be a valid string"),
                ({"date": date(2024, 2, 14), "lunch": 123}, "Input should be a valid string"),
                ({"date": date(2024, 2, 14), "dinner": 123}, "Input should be a valid string"),
                ({"date": date(2024, 2, 14), "dessert": 123}, "Input should be a valid string"),
            ]
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test ScheduleResponse validation."""
            with pytest.raises(ValidationError) as exc_info:
                ScheduleResponse(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test ScheduleResponse model configuration."""
            schema = ScheduleResponse.model_json_schema()
            
            required = schema.get("required", [])
            assert "date" in required
            assert "breakfast" not in required
            assert "lunch" not in required
            assert "dinner" not in required
            assert "dessert" not in required
            
            properties = schema["properties"]
            assert properties["date"]["type"] == "string"
            assert properties["date"]["format"] == "date"
            
            for meal in ["breakfast", "lunch", "dinner", "dessert"]:
                assert meal in properties
                assert "anyOf" in properties[meal]
                types = [t["type"] for t in properties[meal]["anyOf"]]
                assert "string" in types
                assert "null" in types

        def test_json_serialization(self, valid_schedule_data: dict[str, Any]) -> None:
            """Test that schedule data can be properly serialized to JSON."""
            schedule = ScheduleResponse(**valid_schedule_data)
            json_str = schedule.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["date"] == "2024-02-14"
            assert data["breakfast"] == "Pancakes"
            assert data["lunch"] == "Salad"
            assert data["dinner"] == "Steak"
            assert data["dessert"] == "Ice Cream"
