import json
from typing import Any, Literal

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import RecipeSchema, RecipeUpdateSchema


class TestRecipeSchema:
    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions",
        [
            ("Pancakes", "breakfast", ["flour", "milk", "eggs"], ["Mix ingredients", "Cook on pan"]),
            ("Salad", "lunch", ["lettuce", "tomato", "cucumber"], ["Chop vegetables", "Mix together"]),
            ("Steak", "dinner", ["beef", "salt", "pepper"], ["Season steak", "Grill for 10 minutes"]),
        ],
    )
    def test_valid(self, meal_name: str, meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], ingredients: list[str], instructions: list[str]) -> None:
        """Test creating valid RecipeSchema instances."""
        recipe = RecipeSchema(
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions,
        )
        assert recipe.meal_name == meal_name
        assert recipe.meal_type == meal_type
        assert recipe.ingredients == ingredients
        assert recipe.instructions == instructions

    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions",
        [
            ("Pancakes", "breakfast", ["flour", "milk", "eggs"], ["Mix ingredients", "Cook on pan"]),
            ("Salad", "lunch", ["lettuce", "tomato", "cucumber"], ["Chop vegetables", "Mix together"]),
            ("Steak", "dinner", ["beef", "salt", "pepper"], ["Season steak", "Grill for 10 minutes"]),
        ],
    )
    def test_update_valid(self, meal_name: str, meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], ingredients: list[str], instructions: list[str]) -> None:
        """Test creating valid RecipeUpdateSchema instances."""
        recipe = RecipeUpdateSchema(
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions,
        )
        assert recipe.meal_name == meal_name
        assert recipe.meal_type == meal_type
        assert recipe.ingredients == ingredients
        assert recipe.instructions == instructions

    def test_update_partial(self) -> None:
        """Test creating RecipeUpdateSchema with partial data."""
        recipe1 = RecipeUpdateSchema(meal_name="New Recipe")
        assert recipe1.meal_name == "New Recipe"
        assert recipe1.meal_type is None
        assert recipe1.ingredients is None
        assert recipe1.instructions is None

        recipe2 = RecipeUpdateSchema(meal_type="breakfast")
        assert recipe2.meal_name is None
        assert recipe2.meal_type == "breakfast"
        assert recipe2.ingredients is None
        assert recipe2.instructions is None

    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions, expected_error",
        [
            ("", "breakfast", ["eggs"], ["Cook"], "String should have at least 1 character"),
            ("Test", "invalid", ["eggs"], ["Cook"], "Input should be 'breakfast', 'lunch', 'dinner' or 'dessert'"),
            ("Test", "breakfast", [123], ["Cook"], "Input should be a valid string"),
            ("Test", "breakfast", ["eggs"], [123], "Input should be a valid string"),
        ],
    )
    def test_invalid(self, meal_name: str, meal_type: Any, ingredients: list[Any], instructions: list[Any], expected_error: str) -> None:
        """Test validation errors for invalid RecipeSchema data."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeSchema(
                meal_name=meal_name,
                meal_type=meal_type,
                ingredients=ingredients,
                instructions=instructions,
            )
        
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self) -> None:
        """Test validation errors for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeSchema() # type: ignore
        
        error = str(exc_info.value)
        assert "Field required" in error
        assert "meal_name" in error
        assert "meal_type" in error

    def test_invalid_empty_values(self) -> None:
        """Test validation errors for empty values in required fields."""
        with pytest.raises(ValidationError) as excinfo:
            RecipeSchema(
                meal_name="",
                meal_type="breakfast",
                ingredients=[],
                instructions=[]
            )
        
        error = str(excinfo.value)
        assert "meal_name" in error

    def test_update_empty(self) -> None:
        """Test creating empty RecipeUpdateSchema."""
        recipe = RecipeUpdateSchema()
        assert recipe.meal_name is None
        assert recipe.meal_type is None
        assert recipe.ingredients is None
        assert recipe.instructions is None

    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions",
        [
            ("A" * 300, "breakfast", ["eggs"], ["Step 1"]),
            ("Test", "lunch", ["ingredient" * 50], ["Step 1"]),
            ("Test", "dinner", ["Salt"], ["Step" * 100]),
        ],
    )
    def test_edge_cases(self, meal_name: str, meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], ingredients: list[str], instructions: list[str]) -> None:
        """Test edge cases for RecipeSchema."""
        if len(meal_name) > 200:
            with pytest.raises(ValidationError) as exc_info:
                RecipeSchema(
                    meal_name=meal_name,
                    meal_type=meal_type,
                    ingredients=ingredients,
                    instructions=instructions,
                )
            assert "String should have at most 200 characters" in str(exc_info.value)
            return

        recipe = RecipeSchema(
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions,
        )
        assert recipe.meal_name == meal_name
        assert recipe.meal_type == meal_type

    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions",
        [
            (123, "breakfast", ["eggs"], ["Crack the eggs"]), 
            ("Test", "lunch", "Not a list", ["Step 1"]), 
            ("Test", "dinner", ["Salt"], {"step1": "Do something"}),
        ],
    )
    def test_invalid_types(self, meal_name: str, meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], ingredients: list[str], instructions: list[str]) -> None:
        with pytest.raises(ValidationError):
            RecipeSchema(
                meal_name=meal_name, meal_type=meal_type, ingredients=ingredients, instructions=instructions
            )

    @pytest.mark.parametrize(
        "meal_name, meal_type, ingredients, instructions",
        [
            ("Test", "invalid", ["eggs"], ["Crack the eggs"]),
            ("Test", 123, ["eggs"], ["Crack the eggs"]),
            ("Test", None, ["eggs"], ["Crack the eggs"]),
        ],
    )
    def test_invalid_meal_type(self, meal_name: str, meal_type: Any, ingredients: list[str], instructions: list[str]) -> None:
        with pytest.raises(ValidationError):
            RecipeSchema(
                meal_name=meal_name, meal_type=meal_type, ingredients=ingredients, instructions=instructions
            )

    def test_json_serialization(self) -> None:
        """Test that recipe data can be properly serialized to JSON."""
        recipe = RecipeSchema(
            meal_name="Test Recipe",
            meal_type="breakfast",
            ingredients=["ingredient1", "ingredient2"],
            instructions=["step1", "step2"]
        )
        
        json_str = recipe.model_dump_json()
        assert isinstance(json_str, str)
        
        data = json.loads(json_str)
        assert data["ingredients"] == ["ingredient1", "ingredient2"]
        assert data["instructions"] == ["step1", "step2"]

    @pytest.mark.parametrize(
        "update_data",
        [
            {"meal_name": "Updated Recipe"},
            {"meal_type": "lunch"},
            {"ingredients": ["new_ingredient"]},
            {"instructions": ["new_step"]},
            {
                "meal_name": "Full Update",
                "meal_type": "dinner",
                "ingredients": ["ingredient1", "ingredient2"],
                "instructions": ["step1", "step2"]
            },
            {},  # Test empty update
        ],
    )
    def test_update_partial_updates(self, update_data: dict[str, Any]) -> None:
        """Test that RecipeUpdateSchema properly handles partial updates."""
        recipe = RecipeUpdateSchema(**update_data)
        
        # Check if fields match input data
        for field, value in update_data.items():
            assert getattr(recipe, field) == value
        
        # Check if fields not present in update_data are None
        all_fields = {"meal_name", "meal_type", "ingredients", "instructions"}
        for field in all_fields - set(update_data.keys()):
            assert getattr(recipe, field) is None

    @pytest.mark.parametrize(
        "invalid_data,expected_error",
        [
            (
                {"meal_type": "invalid_type"},
                "Input should be 'breakfast', 'lunch', 'dinner' or 'dessert'"
            ),
            (
                {"ingredients": [""]},
                "Input should be a valid string"
            ),
            (
                {"instructions": [""]},
                "Input should be a valid string"
            ),
            (
                {"ingredients": "not_a_list"},
                "Input should be a valid list"
            ),
            (
                {"instructions": {"step1": "not a list"}},
                "Input should be a valid list"
            ),
        ],
    )
    def test_update_validation(self, invalid_data: dict[str, Any], expected_error: str) -> None:
        """Test that RecipeUpdateSchema properly validates input data."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeUpdateSchema(**invalid_data)
        assert expected_error in str(exc_info.value)

    def test_update_type_conversion(self) -> None:
        """Test that RecipeUpdateSchema properly handles input data."""
        update_data = {
            "meal_name": "Recipe Name",
            "meal_type": "breakfast",
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": ["step1", "step2"]
        }
        
        recipe = RecipeUpdateSchema(**update_data)
        
        assert recipe.meal_name == "Recipe Name"
        assert recipe.meal_type == "breakfast"
        assert recipe.ingredients == ["ingredient1", "ingredient2"]
        assert recipe.instructions == ["step1", "step2"]

    @pytest.mark.parametrize(
        "valid_meal_type",
        ["breakfast", "lunch", "dinner", "dessert"]
    )
    def test_update_valid_meal_types(self, valid_meal_type: str) -> None:
        """Test that RecipeUpdateSchema accepts all valid meal types."""
        recipe = RecipeUpdateSchema(meal_type=valid_meal_type)
        assert recipe.meal_type == valid_meal_type

    def test_update_model_config(self) -> None:
        """Test RecipeUpdateSchema model configuration."""
        schema = RecipeUpdateSchema.model_json_schema()
        
        # Check if schema contains appropriate fields
        properties = schema["properties"]
        assert "meal_name" in properties
        assert "meal_type" in properties
        assert "ingredients" in properties
        assert "instructions" in properties
        
        # Check if fields are optional
        assert all(field not in schema.get("required", []) 
                  for field in ["meal_name", "meal_type", "ingredients", "instructions"])

    @pytest.mark.parametrize(
        "invalid_items",
        [
            [" "],  # Only whitespace
            ["valid", "\t"],  # Tab
            ["valid", "  "],  # Multiple whitespaces
        ]
    )
    def test_recipe_schema_whitespace_validation(self, invalid_items: list[str]) -> None:
        """Test that RecipeSchema validates whitespace-only strings."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                ingredients=invalid_items
            )
        assert "Input should be a valid string" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                instructions=invalid_items
            )
        assert "Input should be a valid string" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_items",
        [
            [" "],  # Only whitespace
            ["valid", "\t"],  # Tab
            ["valid", "  "],  # Multiple whitespaces
        ]
    )
    def test_recipe_update_schema_whitespace_validation(self, invalid_items: list[str]) -> None:
        """Test that RecipeUpdateSchema validates whitespace-only strings."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeUpdateSchema(ingredients=invalid_items)
        assert "Input should be a valid string" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RecipeUpdateSchema(instructions=invalid_items)
        assert "Input should be a valid string" in str(exc_info.value)
