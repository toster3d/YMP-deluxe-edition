"""Unit tests for RecipeSchema and RecipeUpdateSchema."""

import json
from typing import Any, Literal

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import MealType, RecipeSchema, RecipeUpdateSchema


@pytest.fixture
def valid_recipe_data() -> dict[str, Any]:
    """Fixture providing valid recipe data."""
    return {
        "meal_name": "Test Recipe",
        "meal_type": "breakfast",
        "ingredients": ["ingredient1", "ingredient2"],
        "instructions": ["step1", "step2"]
    }


@pytest.mark.schema
class TestRecipeSchema:
    """Test suite for RecipeSchema validation and functionality."""
    
    class TestMealNameValidation:
        """Tests for meal_name validation."""

        @pytest.mark.parametrize(
            "meal_name",
            [
                "Simple Recipe",
                "Recipe-123",
                "My's Recipe",
                "Recipe 123",
                "A" * 200,  # Max length
            ]
        )
        def test_valid_meal_names(self, meal_name: str, valid_recipe_data: dict[str, Any]) -> None:
            """Test valid meal names."""
            valid_recipe_data["meal_name"] = meal_name
            recipe = RecipeSchema(**valid_recipe_data)
            assert recipe.meal_name == meal_name

        @pytest.mark.parametrize(
            "invalid_meal_name,expected_error",
            [
                ("", "String should have at least 1 character"),
                (" " * 5, "Meal name cannot be empty or whitespace"),
                ("A" * 201, "String should have at most 200 characters"),
                ("Recipe@123", "String should match pattern"),
                ("Recipe#1", "String should match pattern"),
            ]
        )
        def test_invalid_meal_names(
            self, invalid_meal_name: str, expected_error: str, valid_recipe_data: dict[str, Any]
        ) -> None:
            """Test invalid meal names."""
            valid_recipe_data["meal_name"] = invalid_meal_name
            with pytest.raises(ValidationError) as exc_info:
                RecipeSchema(**valid_recipe_data)
            assert expected_error in str(exc_info.value)

    class TestMealTypeValidation:
        """Tests for meal_type validation."""

        @pytest.mark.parametrize("meal_type", ["breakfast", "lunch", "dinner", "dessert"])
        def test_valid_meal_types(self, meal_type: MealType, valid_recipe_data: dict[str, Any]) -> None:
            """Test valid meal types."""
            valid_recipe_data["meal_type"] = meal_type
            recipe = RecipeSchema(**valid_recipe_data)
            assert recipe.meal_type == meal_type

        @pytest.mark.parametrize(
            "invalid_meal_type",
            [
                "brunch",
                "snack",
                "",
                "BREAKFAST",
                "Lunch",
                123,
                None,
            ]
        )
        def test_invalid_meal_types(self, invalid_meal_type: Any, valid_recipe_data: dict[str, Any]) -> None:
            """Test invalid meal types."""
            valid_recipe_data["meal_type"] = invalid_meal_type
            with pytest.raises(ValidationError) as exc_info:
                RecipeSchema(**valid_recipe_data)
            assert "Input should be 'breakfast', 'lunch', 'dinner' or 'dessert'" in str(exc_info.value)

    class TestIngredientsValidation:
        """Tests for ingredients validation."""

        @pytest.mark.parametrize(
            "ingredients",
            [
                [],  # Empty list is allowed
                ["flour"],  # Single ingredient
                ["flour", "sugar", "eggs"],  # Multiple ingredients
                ["ingredient" * 10],  # Long ingredient name
                ["a"],  # Minimal length
            ]
        )
        def test_valid_ingredients(self, ingredients: list[str], valid_recipe_data: dict[str, Any]) -> None:
            """Test valid ingredients lists."""
            valid_recipe_data["ingredients"] = ingredients
            recipe = RecipeSchema(**valid_recipe_data)
            assert recipe.ingredients == ingredients

        @pytest.mark.parametrize(
            "invalid_ingredients,expected_error",
            [
                ([""], "Each item must be a non-empty string"),
                ([" "], "Each item must be a non-empty string"),
                (["valid", ""], "Each item must be a non-empty string"),
                (["valid", None], "Input should be a valid string"),
                (None, "Input should be a valid list"),
                ("not a list", "Input should be a valid list"),
            ]
        )
        def test_invalid_ingredients(
            self, invalid_ingredients: Any, expected_error: str, valid_recipe_data: dict[str, Any]
        ) -> None:
            """Test invalid ingredients lists."""
            valid_recipe_data["ingredients"] = invalid_ingredients
            with pytest.raises(ValidationError) as exc_info:
                RecipeSchema(**valid_recipe_data)
            assert expected_error in str(exc_info.value)

    class TestInstructionsValidation:
        """Tests for instructions validation."""

        @pytest.mark.parametrize(
            "instructions",
            [
                [],  # Empty list is allowed
                ["Mix well"],  # Single instruction
                ["Prepare", "Mix", "Bake"],  # Multiple instructions
                ["Step " * 10],  # Long instruction
                ["1"],  # Minimal length
            ]
        )
        def test_valid_instructions(self, instructions: list[str], valid_recipe_data: dict[str, Any]) -> None:
            """Test valid instructions lists."""
            valid_recipe_data["instructions"] = instructions
            recipe = RecipeSchema(**valid_recipe_data)
            assert recipe.instructions == instructions

        @pytest.mark.parametrize(
            "invalid_instructions,expected_error",
            [
                ([""], "Each item must be a non-empty string"),
                ([" "], "Each item must be a non-empty string"),
                (["valid", ""], "Each item must be a non-empty string"),
                (["valid", None], "Input should be a valid string"),
                (None, "Input should be a valid list"),
                ("not a list", "Input should be a valid list"),
            ]
        )
        def test_invalid_instructions(
            self, invalid_instructions: Any, expected_error: str, valid_recipe_data: dict[str, Any]
        ) -> None:
            """Test invalid instructions lists."""
            valid_recipe_data["instructions"] = invalid_instructions
            with pytest.raises(ValidationError) as exc_info:
                RecipeSchema(**valid_recipe_data)
            assert expected_error in str(exc_info.value)

    class TestSchemaConfiguration:
        """Tests for schema configuration and serialization."""

        def test_model_config(self) -> None:
            """Test RecipeSchema model configuration."""
            schema = RecipeSchema.model_json_schema()
            
            # Test required fields
            required = schema.get("required", [])
            assert "meal_name" in required
            assert "meal_type" in required
            
            # Test field properties
            properties = schema["properties"]
            
            assert properties["meal_name"]["type"] == "string"
            assert properties["meal_name"]["minLength"] == 1
            assert properties["meal_name"]["maxLength"] == 200
            
            assert properties["meal_type"]["type"] == "string"
            assert "enum" in properties["meal_type"]
            
            assert properties["ingredients"]["type"] == "array"
            assert properties["ingredients"]["items"]["type"] == "string"
            
            assert properties["instructions"]["type"] == "array"
            assert properties["instructions"]["items"]["type"] == "string"

        def test_json_serialization(self, valid_recipe_data: dict[str, Any]) -> None:
            """Test JSON serialization and deserialization."""
            recipe = RecipeSchema(**valid_recipe_data)
            json_str = recipe.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            for field, value in valid_recipe_data.items():
                assert data[field] == value

            # Test round trip
            recipe_2 = RecipeSchema(**data)
            assert recipe_2.model_dump() == valid_recipe_data

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
    def test_invalid_types(self, meal_name: Any, meal_type: Any, ingredients: Any, instructions: Any) -> None:
        """Test validation errors for invalid types."""
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
        """Test validation errors for invalid meal types."""
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
        recipe = RecipeUpdateSchema(
            meal_name="Recipe Name",
            meal_type="breakfast",
            ingredients=["ingredient1", "ingredient2"],
            instructions=["step1", "step2"]
        )
        
        assert recipe.meal_name == "Recipe Name"
        assert recipe.meal_type == "breakfast"
        assert recipe.ingredients == ["ingredient1", "ingredient2"]
        assert recipe.instructions == ["step1", "step2"]

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
        assert "Each item must be a non-empty string" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RecipeSchema(
                meal_name="Test Recipe",
                meal_type="breakfast",
                instructions=invalid_items
            )
        assert "Each item must be a non-empty string" in str(exc_info.value)

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
