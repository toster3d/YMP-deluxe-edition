"""Unit tests for shopping list related schemas."""

import json
from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import (
    DateRangeSchema,
    ShoppingListRangeResponse,
    ShoppingListResponse,
)


@pytest.mark.schema
class TestShoppingListResponse:
    """Test suite for ShoppingListResponse validation and functionality."""

    @pytest.fixture
    def valid_shopping_list_data(self) -> dict[str, Any]:
        """Fixture providing valid shopping list data."""
        return {
            "ingredients": ["flour", "milk", "eggs"],
            "current_date": "2024-02-14"
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_shopping_list_data: dict[str, Any]) -> None:
            """Test valid ShoppingListResponse creation."""
            shopping_list = ShoppingListResponse(**valid_shopping_list_data)
            assert shopping_list.ingredients == ["flour", "milk", "eggs"]
            assert shopping_list.current_date == "2024-02-14"

        def test_empty_ingredients(self) -> None:
            """Test ShoppingListResponse with empty ingredients list."""
            shopping_list = ShoppingListResponse(
                ingredients=[],
                current_date="2024-02-14"
            )
            assert shopping_list.ingredients == []
            assert shopping_list.current_date == "2024-02-14"

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"current_date": "2024-02-14"}, "Field required"),
                ({"ingredients": ["flour", "milk"]}, "Field required"),
                ({"ingredients": "not_a_list", "current_date": "2024-02-14"}, "Input should be a valid list"),
                ({"ingredients": [123, 456], "current_date": "2024-02-14"}, "Input should be a valid string"),
            ]
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test ShoppingListResponse validation."""
            with pytest.raises(ValidationError) as exc_info:
                ShoppingListResponse(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestIngredientsValidation:
        """Tests for ingredients list validation."""

        @pytest.mark.parametrize(
            "ingredients",
            [
                ["flour"],
                ["flour", "milk", "eggs"],
                ["flour", "milk", "eggs"] * 10,
                ["salt", "pepper", "sugar", "vanilla extract"],
                ["1 cup flour", "2 tbsp sugar", "3 eggs"],
            ]
        )
        def test_various_ingredients(self, ingredients: list[str]) -> None:
            """Test ShoppingListResponse with different ingredients lists."""
            shopping_list = ShoppingListResponse(
                ingredients=ingredients,
                current_date="2024-02-14"
            )
            assert shopping_list.ingredients == ingredients

        @pytest.mark.parametrize(
            "invalid_ingredients,expected_error",
            [
                ([123, 456], "Input should be a valid string"),
                (["flour", None], "Input should be a valid string"),
            ]
        )
        def test_invalid_ingredients(self, invalid_ingredients: list[Any], expected_error: str) -> None:
            """Test validation of invalid ingredients."""
            with pytest.raises(ValidationError) as exc_info:
                ShoppingListResponse(
                    ingredients=invalid_ingredients,
                    current_date="2024-02-14"
                )
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test ShoppingListResponse model configuration."""
            schema = ShoppingListResponse.model_json_schema()
            
            required = schema.get("required", [])
            assert "ingredients" in required
            assert "current_date" in required
            
            properties = schema["properties"]
            assert properties["ingredients"]["type"] == "array"
            assert properties["ingredients"]["items"]["type"] == "string"
            assert properties["current_date"]["type"] == "string"
            
            assert "description" in properties["ingredients"]
            assert "description" in properties["current_date"]

        def test_json_serialization(self, valid_shopping_list_data: dict[str, Any]) -> None:
            """Test JSON serialization and deserialization."""
            shopping_list = ShoppingListResponse(**valid_shopping_list_data)
            json_str = shopping_list.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["ingredients"] == ["flour", "milk", "eggs"]
            assert data["current_date"] == "2024-02-14"


@pytest.mark.schema
class TestShoppingListRangeResponse:
    """Test suite for ShoppingListRangeResponse validation and functionality."""

    @pytest.fixture
    def valid_range_data(self) -> dict[str, Any]:
        """Fixture providing valid range data."""
        return {
            "ingredients": ["flour", "milk", "eggs"],
            "date_range": "2024-02-14 to 2024-02-21"
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_range_data: dict[str, Any]) -> None:
            """Test valid ShoppingListRangeResponse creation."""
            shopping_list = ShoppingListRangeResponse(**valid_range_data)
            assert shopping_list.ingredients == ["flour", "milk", "eggs"]
            assert shopping_list.date_range == "2024-02-14 to 2024-02-21"

        def test_empty_ingredients(self) -> None:
            """Test ShoppingListRangeResponse with empty ingredients list."""
            shopping_list = ShoppingListRangeResponse(
                ingredients=[],
                date_range="2024-02-14 to 2024-02-21"
            )
            assert shopping_list.ingredients == []
            assert shopping_list.date_range == "2024-02-14 to 2024-02-21"

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"date_range": "2024-02-14 to 2024-02-21"}, "Field required"),
                ({"ingredients": ["flour", "milk"]}, "Field required"),
                ({"ingredients": "not_a_list", "date_range": "2024-02-14 to 2024-02-21"}, "Input should be a valid list"),
                ({"ingredients": [123, 456], "date_range": "2024-02-14 to 2024-02-21"}, "Input should be a valid string"),
            ]
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test ShoppingListRangeResponse validation."""
            with pytest.raises(ValidationError) as exc_info:
                ShoppingListRangeResponse(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test ShoppingListRangeResponse model configuration."""
            schema = ShoppingListRangeResponse.model_json_schema()
            
            required = schema.get("required", [])
            assert "ingredients" in required
            assert "date_range" in required
            
            properties = schema["properties"]
            assert properties["ingredients"]["type"] == "array"
            assert properties["ingredients"]["items"]["type"] == "string"
            assert properties["date_range"]["type"] == "string"
            
            assert "description" in properties["ingredients"]
            assert "description" in properties["date_range"]

        def test_json_serialization(self, valid_range_data: dict[str, Any]) -> None:
            """Test JSON serialization and deserialization."""
            shopping_list = ShoppingListRangeResponse(**valid_range_data)
            json_str = shopping_list.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["ingredients"] == ["flour", "milk", "eggs"]
            assert data["date_range"] == "2024-02-14 to 2024-02-21"


@pytest.mark.schema
class TestDateRangeSchema:
    """Test suite for DateRangeSchema validation and functionality."""

    @pytest.fixture
    def valid_date_range_data(self) -> dict[str, Any]:
        """Fixture providing valid date range data."""
        return {
            "start_date": date(2024, 2, 14),
            "end_date": date(2024, 2, 21)
        }

    class TestRequiredFields:
        """Tests for required fields validation."""

        def test_valid(self, valid_date_range_data: dict[str, Any]) -> None:
            """Test valid DateRangeSchema creation."""
            date_range = DateRangeSchema(**valid_date_range_data)
            assert date_range.start_date == date(2024, 2, 14)
            assert date_range.end_date == date(2024, 2, 21)

        @pytest.mark.parametrize(
            "start_date,end_date",
            [
                (date(2024, 2, 14), date(2024, 2, 21)),
                (date(2024, 2, 14), date(2024, 2, 14)),
                (date(2024, 1, 1), date(2024, 12, 31)),
                (date(2024, 2, 14), date(2025, 2, 14)),
                (date(2024, 12, 31), date(2025, 1, 1)),
            ]
        )
        def test_valid_ranges(self, start_date: date, end_date: date) -> None:
            """Test DateRangeSchema with different valid date ranges."""
            date_range = DateRangeSchema(
                start_date=start_date,
                end_date=end_date
            )
            assert date_range.start_date == start_date
            assert date_range.end_date == end_date

        @pytest.mark.parametrize(
            "invalid_data,expected_error",
            [
                ({"end_date": date(2024, 2, 21)}, "Field required"),
                ({"start_date": date(2024, 2, 14)}, "Field required"),
                ({"start_date": "invalid_date", "end_date": date(2024, 2, 21)}, "Input should be a valid date"),
                ({"start_date": date(2024, 2, 14), "end_date": "invalid_date"}, "Input should be a valid date"),
            ]
        )
        def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
            """Test DateRangeSchema validation."""
            with pytest.raises(ValidationError) as exc_info:
                DateRangeSchema(**invalid_data)
            assert expected_error in str(exc_info.value)

    class TestModelConfiguration:
        """Tests for model configuration and serialization."""

        def test_model_config(self) -> None:
            """Test DateRangeSchema model configuration."""
            schema = DateRangeSchema.model_json_schema()
            
            required = schema.get("required", [])
            assert "start_date" in required
            assert "end_date" in required
            
            properties = schema["properties"]
            assert properties["start_date"]["type"] == "string"
            assert properties["start_date"]["format"] == "date"
            assert properties["end_date"]["type"] == "string"
            assert properties["end_date"]["format"] == "date"
            
            assert "description" in properties["start_date"]
            assert "description" in properties["end_date"]

        def test_json_serialization(self, valid_date_range_data: dict[str, Any]) -> None:
            """Test JSON serialization and deserialization."""
            date_range = DateRangeSchema(**valid_date_range_data)
            json_str = date_range.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            assert data["start_date"] == "2024-02-14"
            assert data["end_date"] == "2024-02-21"
