from typing import Any, Literal

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import RecipeSchema, RecipeUpdateSchema


@pytest.mark.parametrize(
    "meal_name, meal_type, ingredients, instructions",
    [
        ("Pancakes", "breakfast", ["flour", "milk", "eggs"], ["Mix ingredients", "Cook on pan"]),
        ("Salad", "lunch", ["lettuce", "tomato", "cucumber"], ["Chop vegetables", "Mix together"]),
        ("Steak", "dinner", ["beef", "salt", "pepper"], ["Season steak", "Grill for 10 minutes"]),
    ],
)
def test_recipe_schema_valid(
    meal_name: str, 
    meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], 
    ingredients: list[str], 
    instructions: list[str]
) -> None:
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
def test_recipe_update_schema_valid(
    meal_name: str, 
    meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], 
    ingredients: list[str], 
    instructions: list[str]
) -> None:
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


def test_recipe_update_schema_partial() -> None:
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
def test_recipe_schema_invalid(
    meal_name: str,
    meal_type: Any,
    ingredients: list[Any],
    instructions: list[Any],
    expected_error: str,
) -> None:
    """Test validation errors for invalid RecipeSchema data."""
    with pytest.raises(ValidationError) as exc_info:
        RecipeSchema(
            meal_name=meal_name,
            meal_type=meal_type,
            ingredients=ingredients,
            instructions=instructions,
        )
    
    assert expected_error in str(exc_info.value)


def test_recipe_schema_missing_required_fields() -> None:
    """Test validation errors for missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        RecipeSchema() # type: ignore
    
    error = str(exc_info.value)
    assert "Field required" in error
    assert "meal_name" in error
    assert "meal_type" in error


def test_recipe_schema_invalid_empty_values() -> None:
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


def test_recipe_update_schema_empty() -> None:
    """Test creating empty RecipeUpdateSchema."""
    recipe = RecipeUpdateSchema()
    assert recipe.meal_name is None
    assert recipe.meal_type is None
    assert recipe.ingredients is None
    assert recipe.instructions is None

# Test additional cases
@pytest.mark.parametrize(
    "meal_name, meal_type, ingredients, instructions",
    [
        ("A" * 300, "breakfast", ["eggs"], ["Step 1"]),
        ("Test", "lunch", ["ingredient" * 50], ["Step 1"]),
        ("Test", "dinner", ["Salt"], ["Step" * 100]),
    ],
)
def test_recipe_schema_edge_cases(
    meal_name: str, 
    meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], 
    ingredients: list[str], 
    instructions: list[str]
) -> None:
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
def test_recipe_schema_invalid_types(meal_name: str, meal_type: Literal["breakfast", "lunch", "dinner", "dessert"], ingredients: list[str], instructions: list[str]) -> None:
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
def test_recipe_schema_invalid_meal_type(meal_name: str, meal_type: Any, ingredients: list[str], instructions: list[str]) -> None:
    with pytest.raises(ValidationError):
        RecipeSchema(
            meal_name=meal_name, meal_type=meal_type, ingredients=ingredients, instructions=instructions
        )

def test_recipe_json_serialization() -> None:
    """Test that recipe data can be properly serialized to JSON."""
    import json
    
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