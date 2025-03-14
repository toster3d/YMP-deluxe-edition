import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.resources.pydantic_schemas import RecipeSchema, RecipeUpdateSchema
from src.services.recipe_manager import RecipeManager
from tests.test_models.models_db_test import TestRecipe, TestUser


@pytest.fixture
async def recipe_manager(db_session: AsyncSession) -> RecipeManager:
    """Fixture providing a RecipeManager instance with a test database session."""
    return RecipeManager(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> TestUser:
    """Create a test user for recipe manager tests."""
    user = TestUser(
        user_name="recipe_manager_test_user",
        email="recipe_manager_test@example.com",
        hash="hashedpassword"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_recipes(db_session: AsyncSession, test_user: TestUser) -> list[TestRecipe]:
    """Create multiple test recipes for a user."""
    recipes = [
        TestRecipe(
            user_id=test_user.id,
            meal_name="Test Breakfast",
            meal_type="breakfast",
            ingredients=json.dumps(["eggs", "bread", "butter"]),
            instructions=json.dumps(["cook eggs", "toast bread", "serve"])
        ),
        TestRecipe(
            user_id=test_user.id,
            meal_name="Test Lunch",
            meal_type="lunch",
            ingredients=json.dumps(["chicken", "rice", "vegetables"]),
            instructions=json.dumps(["cook chicken", "boil rice", "serve"])
        ),
        TestRecipe(
            user_id=test_user.id,
            meal_name="Test Dinner",
            meal_type="dinner",
            ingredients=json.dumps(["beef", "potatoes", "gravy"]),
            instructions=json.dumps(["cook beef", "mash potatoes", "serve"])
        )
    ]
    
    for recipe in recipes:
        db_session.add(recipe)
    
    await db_session.commit()
    
    # Refresh to get IDs
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    return recipes


@pytest.mark.asyncio
async def test_get_recipes_empty(recipe_manager: RecipeManager, test_user: TestUser) -> None:
    """Test getting recipes when user has no recipes."""
    # Act
    recipes = await recipe_manager.get_recipes(test_user.id)
    
    # Assert
    assert isinstance(recipes, list)
    assert len(recipes) == 0


@pytest.mark.asyncio
async def test_get_recipes_multiple(
    recipe_manager: RecipeManager, 
    test_user: TestUser,
    test_recipes: list[TestRecipe]
) -> None:
    """Test getting multiple recipes for a user."""
    # Act
    recipes = await recipe_manager.get_recipes(test_user.id)
    
    # Assert
    assert isinstance(recipes, list)
    assert len(recipes) == 3
    
    # Verify recipe data
    meal_names = [recipe.meal_name for recipe in recipes]
    assert "Test Breakfast" in meal_names
    assert "Test Lunch" in meal_names
    assert "Test Dinner" in meal_names
    
    # Check that ingredients and instructions are properly deserialized
    for recipe in recipes:
        if recipe.meal_name == "Test Breakfast":
            assert recipe.meal_type == "breakfast"
            assert isinstance(recipe.ingredients, list)
            assert "eggs" in recipe.ingredients
            assert isinstance(recipe.instructions, list)
            assert "cook eggs" in recipe.instructions


@pytest.mark.asyncio
async def test_get_recipe_by_id_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe]
) -> None:
    """Test getting a recipe by ID when it exists."""
    # Arrange
    recipe_id = test_recipes[0].id
    
    # Act
    recipe = await recipe_manager.get_recipe_by_id(recipe_id, test_user.id)
    
    # Assert
    assert recipe is not None
    assert hasattr(recipe, "meal_name")
    assert hasattr(recipe, "meal_type")
    assert hasattr(recipe, "ingredients")
    assert hasattr(recipe, "instructions")


@pytest.mark.asyncio
async def test_get_recipe_by_id_not_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser
) -> None:
    """Test getting a recipe by ID when it doesn't exist."""
    # Act
    recipe = await recipe_manager.get_recipe_by_id(999, test_user.id)
    
    # Assert
    assert recipe is None


@pytest.mark.asyncio
async def test_get_recipe_by_id_wrong_user(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe],
    db_session: AsyncSession
) -> None:
    """Test getting a recipe by ID with wrong user ID."""
    # Arrange
    recipe_id = test_recipes[0].id
    
    # Create another user
    other_user = TestUser(
        user_name="other_user",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Act
    recipe = await recipe_manager.get_recipe_by_id(recipe_id, other_user.id)
    
    # Assert
    assert recipe is None


@pytest.mark.asyncio
async def test_get_recipe_details(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe]
) -> None:
    """Test getting complete recipe details."""
    # Arrange
    recipe_id = test_recipes[0].id
    
    # Act
    recipe = await recipe_manager.get_recipe_details(recipe_id, test_user.id)
    
    # Assert
    assert recipe is not None
    assert hasattr(recipe, "meal_name")
    assert hasattr(recipe, "meal_type")
    assert hasattr(recipe, "ingredients")
    assert hasattr(recipe, "instructions")


@pytest.mark.asyncio
async def test_get_recipe_by_name(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe]
) -> None:
    """Test finding a recipe by name."""
    # Act
    recipe = await recipe_manager.get_recipe_by_name(test_user.id, "Test Lunch")
    
    # Assert
    assert recipe is not None
    assert recipe.meal_name == "Test Lunch"
    assert recipe.meal_type == "lunch"
    assert "chicken" in recipe.ingredients
    assert "cook chicken" in recipe.instructions


@pytest.mark.asyncio
async def test_get_recipe_by_name_not_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser
) -> None:
    """Test finding a recipe by name that doesn't exist."""
    # Act
    recipe = await recipe_manager.get_recipe_by_name(test_user.id, "Nonexistent Recipe")
    
    # Assert
    assert recipe is None


@pytest.mark.asyncio
async def test_add_recipe(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    db_session: AsyncSession
) -> None:
    """Test adding a new recipe."""
    # Arrange
    recipe_data = RecipeSchema(
        meal_name="New Test Recipe",
        meal_type="dessert",
        ingredients=["sugar", "flour", "eggs"],
        instructions=["mix ingredients", "bake", "serve"]
    )
    
    # Act
    recipe = await recipe_manager.add_recipe(test_user.id, recipe_data)
    
    # Assert
    assert recipe is not None
    assert recipe.meal_name == "New Test Recipe"
    assert recipe.meal_type == "dessert"
    
    # Verify in database
    query = select(TestRecipe).filter_by(id=recipe.id)
    result = await db_session.execute(query)
    db_recipe = result.scalar_one_or_none()
    
    assert db_recipe is not None
    assert db_recipe.meal_name == "New Test Recipe"
    assert db_recipe.meal_type == "dessert"
    assert json.loads(db_recipe.ingredients) == ["sugar", "flour", "eggs"]
    assert json.loads(db_recipe.instructions) == ["mix ingredients", "bake", "serve"]


@pytest.mark.asyncio
async def test_update_recipe(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe],
    db_session: AsyncSession
) -> None:
    """Test updating an existing recipe."""
    # Arrange
    recipe_id = test_recipes[0].id
    update_data = RecipeUpdateSchema(
        meal_name="Updated Recipe Name",
        meal_type="dinner",
        ingredients=["updated ingredient 1", "updated ingredient 2"],
        instructions=["updated step 1", "updated step 2"]
    )
    
    # Act
    updated_recipe = await recipe_manager.update_recipe(recipe_id, test_user.id, update_data)
    
    # Assert
    assert updated_recipe is not None
    assert updated_recipe.meal_name == "Updated Recipe Name"
    assert updated_recipe.meal_type == "dinner"
    
    # Verify in database
    await db_session.refresh(updated_recipe)
    assert updated_recipe.meal_name == "Updated Recipe Name"
    assert updated_recipe.meal_type == "dinner"
    assert json.loads(updated_recipe.ingredients) == ["updated ingredient 1", "updated ingredient 2"]
    assert json.loads(updated_recipe.instructions) == ["updated step 1", "updated step 2"]


@pytest.mark.asyncio
async def test_update_recipe_partial(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe],
    db_session: AsyncSession
) -> None:
    """Test partial update of a recipe (only some fields)."""
    # Arrange
    recipe_id = test_recipes[1].id
    original_meal_type = test_recipes[1].meal_type
    original_ingredients = json.loads(test_recipes[1].ingredients)
    original_instructions = json.loads(test_recipes[1].instructions)
    
    # Only update the name
    update_data = RecipeUpdateSchema(
        meal_name="Partially Updated Recipe",
        meal_type=None,
        ingredients=None,
        instructions=None
    )
    
    # Act
    updated_recipe = await recipe_manager.update_recipe(recipe_id, test_user.id, update_data)
    
    # Assert
    assert updated_recipe is not None
    assert updated_recipe.meal_name == "Partially Updated Recipe"
    assert updated_recipe.meal_type == original_meal_type
    
    # Verify in database
    await db_session.refresh(updated_recipe)
    assert updated_recipe.meal_name == "Partially Updated Recipe"
    assert updated_recipe.meal_type == original_meal_type
    assert json.loads(updated_recipe.ingredients) == original_ingredients
    assert json.loads(updated_recipe.instructions) == original_instructions


@pytest.mark.asyncio
async def test_update_recipe_not_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser
) -> None:
    """Test updating a recipe that doesn't exist."""
    # Arrange
    update_data = RecipeUpdateSchema(
        meal_name="This Won't Update",
        meal_type="dinner",
        ingredients=["ingredient"],
        instructions=["instruction"]
    )
    
    # Act
    result = await recipe_manager.update_recipe(999, test_user.id, update_data)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_delete_recipe(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe],
    db_session: AsyncSession
) -> None:
    """Test deleting a recipe."""
    # Arrange
    recipe_id = test_recipes[0].id
    
    # Act
    result = await recipe_manager.delete_recipe(recipe_id, test_user.id)
    
    # Assert
    assert result is True
    
    # Verify in database
    query = select(TestRecipe).filter_by(id=recipe_id)
    result = await db_session.execute(query)
    recipe = result.scalar_one_or_none()
    assert recipe is None


@pytest.mark.asyncio
async def test_delete_recipe_not_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser
) -> None:
    """Test deleting a recipe that doesn't exist."""
    # Act
    result = await recipe_manager.delete_recipe(999, test_user.id)
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_recipe_wrong_user(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe],
    db_session: AsyncSession
) -> None:
    """Test deleting a recipe with wrong user ID."""
    # Arrange
    recipe_id = test_recipes[0].id
    
    # Create another user
    other_user = TestUser(
        user_name="other_user",
        email="other@example.com",
        hash="hashedpassword"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    
    # Act
    result = await recipe_manager.delete_recipe(recipe_id, other_user.id)
    
    # Assert
    assert result is False
    
    # Verify recipe still exists
    query = select(TestRecipe).filter_by(id=recipe_id)
    db_result = await db_session.execute(query)
    recipe = db_result.scalar_one_or_none()
    assert recipe is not None


@pytest.mark.asyncio
async def test_get_ingredients_by_meal_name(
    recipe_manager: RecipeManager,
    test_user: TestUser,
    test_recipes: list[TestRecipe]
) -> None:
    """Test retrieving ingredients for a recipe by meal name."""
    # Act
    ingredients = await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Test Breakfast")
    
    # Assert
    assert ingredients is not None
    assert isinstance(ingredients, list)
    assert "eggs" in ingredients
    assert "bread" in ingredients
    assert "butter" in ingredients


@pytest.mark.asyncio
async def test_get_ingredients_by_meal_name_not_exists(
    recipe_manager: RecipeManager,
    test_user: TestUser
) -> None:
    """Test retrieving ingredients for a nonexistent recipe."""
    # Act
    ingredients = await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Nonexistent Recipe")
    
    # Assert
    assert ingredients is None
