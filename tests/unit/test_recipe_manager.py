import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
    
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    return recipes


class TestRecipeManager:
    """Test suite for RecipeManager."""

    class TestGetRecipes:
        """Tests for get_recipes method."""

        @pytest.mark.asyncio
        async def test_get_recipes_empty(self, recipe_manager: RecipeManager, test_user: TestUser) -> None:
            """Test getting recipes when user has no recipes."""
            recipes = await recipe_manager.get_recipes(test_user.id)
            
            assert isinstance(recipes, list)
            assert len(recipes) == 0

        @pytest.mark.asyncio
        async def test_get_recipes_multiple(
            self, recipe_manager: RecipeManager, 
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test getting multiple recipes for a user."""
            recipes = await recipe_manager.get_recipes(test_user.id)
            
            assert isinstance(recipes, list)
            assert len(recipes) == 3
            
            meal_names = [recipe.meal_name for recipe in recipes]
            assert "Test Breakfast" in meal_names
            assert "Test Lunch" in meal_names
            assert "Test Dinner" in meal_names
            
            for recipe in recipes:
                if recipe.meal_name == "Test Breakfast":
                    assert recipe.meal_type == "breakfast"
                    assert isinstance(recipe.ingredients, list)
                    assert "eggs" in recipe.ingredients
                    assert isinstance(recipe.instructions, list)
                    assert "cook eggs" in recipe.instructions

        @pytest.mark.asyncio
        async def test_get_recipes_database_error(self) -> None:
            """Test handling database error when getting recipes."""
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            
            recipe_manager = RecipeManager(mock_session)
            
            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.get_recipes(1)
            
            assert "Database error" in str(exc_info.value)
            assert mock_session.execute.called

    class TestGetRecipeById:
        """Tests for get_recipe_by_id method."""

        @pytest.mark.asyncio
        async def test_get_recipe_by_id_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test getting a recipe by ID when it exists."""
            recipe_id = test_recipes[0].id
            
            recipe = await recipe_manager.get_recipe_by_id(recipe_id, test_user.id)
            
            assert recipe is not None
            assert recipe.meal_name == test_recipes[0].meal_name
            assert recipe.meal_type == test_recipes[0].meal_type
            assert isinstance(recipe.ingredients, list)
            assert isinstance(recipe.instructions, list)

        @pytest.mark.asyncio
        async def test_get_recipe_by_id_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test getting a recipe by ID when it doesn't exist."""
            recipe = await recipe_manager.get_recipe_by_id(999, test_user.id)
            
            assert recipe is None

        @pytest.mark.asyncio
        async def test_get_recipe_by_id_wrong_user(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test getting a recipe by ID with wrong user ID."""
            recipe_id = test_recipes[0].id
            
            other_user = TestUser(
                user_name="other_user",
                email="other@example.com",
                hash="hashedpassword"
            )
            db_session.add(other_user)
            await db_session.commit()
            await db_session.refresh(other_user)
            
            recipe = await recipe_manager.get_recipe_by_id(recipe_id, other_user.id)
            
            assert recipe is None

        @pytest.mark.asyncio
        async def test_get_recipe_by_id_database_error(self, test_user: TestUser) -> None:
            """Test handling database error when getting recipe by ID."""
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            
            recipe_manager = RecipeManager(mock_session)
            
            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.get_recipe_by_id(1, test_user.id)
            
            assert "Database error" in str(exc_info.value)
            assert mock_session.execute.called

    class TestGetRecipeDetails:
        """Tests for get_recipe_details method."""

        @pytest.mark.asyncio
        async def test_get_recipe_details(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test getting complete recipe details."""
            recipe_id = test_recipes[0].id
            
            recipe = await recipe_manager.get_recipe_details(recipe_id, test_user.id)
            
            assert recipe is not None
            assert recipe.meal_name == test_recipes[0].meal_name
            assert recipe.meal_type == test_recipes[0].meal_type
            assert isinstance(recipe.ingredients, list)
            assert isinstance(recipe.instructions, list)

        @pytest.mark.asyncio
        async def test_get_recipe_details_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test getting recipe details when it doesn't exist."""
            recipe = await recipe_manager.get_recipe_details(999, test_user.id)
            
            assert recipe is None

    class TestGetRecipeByName:
        """Tests for get_recipe_by_name method."""

        @pytest.mark.asyncio
        async def test_get_recipe_by_name(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test finding a recipe by name."""
            recipe = await recipe_manager.get_recipe_by_name(test_user.id, "Test Lunch")
            
            assert recipe is not None
            assert recipe.meal_name == "Test Lunch"
            assert recipe.meal_type == "lunch"
            assert "chicken" in recipe.ingredients
            assert "cook chicken" in recipe.instructions

        @pytest.mark.asyncio
        async def test_get_recipe_by_name_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test finding a recipe by name that doesn't exist."""
            recipe = await recipe_manager.get_recipe_by_name(test_user.id, "Nonexistent Recipe")
            
            assert recipe is None

        @pytest.mark.asyncio
        async def test_get_recipe_by_name_case_sensitive(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test that recipe name search is case sensitive."""
            recipe = await recipe_manager.get_recipe_by_name(test_user.id, "test lunch")
            
            assert recipe is None

    class TestAddRecipe:
        """Tests for add_recipe method."""

        @pytest.mark.asyncio
        async def test_add_recipe(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test adding a new recipe."""
            recipe_data = RecipeSchema(
                meal_name="New Test Recipe",
                meal_type="dessert",
                ingredients=["sugar", "flour", "eggs"],
                instructions=["mix ingredients", "bake", "serve"]
            )
            
            recipe = await recipe_manager.add_recipe(test_user.id, recipe_data)
            
            assert recipe is not None
            assert recipe.meal_name == "New Test Recipe"
            assert recipe.meal_type == "dessert"
            
            query = select(TestRecipe).filter_by(id=recipe.id)
            result = await db_session.execute(query)
            db_recipe = result.scalar_one_or_none()
            
            assert db_recipe is not None
            assert db_recipe.meal_name == "New Test Recipe"
            assert db_recipe.meal_type == "dessert"
            assert json.loads(db_recipe.ingredients) == ["sugar", "flour", "eggs"]
            assert json.loads(db_recipe.instructions) == ["mix ingredients", "bake", "serve"]

        @pytest.mark.asyncio
        async def test_add_recipe_with_empty_lists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test adding a recipe with empty ingredients and instructions lists."""
            recipe_data = RecipeSchema(
                meal_name="Recipe With Empty Lists",
                meal_type="breakfast",
                ingredients=[],
                instructions=[]
            )
            
            recipe = await recipe_manager.add_recipe(test_user.id, recipe_data)
            
            assert recipe is not None
            assert recipe.meal_name == "Recipe With Empty Lists"
            assert recipe.meal_type == "breakfast"
            
            query = select(TestRecipe).filter_by(id=recipe.id)
            result = await db_session.execute(query)
            db_recipe = result.scalar_one_or_none()
            
            assert db_recipe is not None
            assert db_recipe.meal_name == "Recipe With Empty Lists"
            assert db_recipe.meal_type == "breakfast"
            assert json.loads(db_recipe.ingredients) == []
            assert json.loads(db_recipe.instructions) == []

        @pytest.mark.asyncio
        async def test_add_recipe_database_error(self, test_user: TestUser) -> None:
            """Test handling database error when adding a recipe."""
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            
            recipe_manager = RecipeManager(mock_session)
            
            recipe_data = RecipeSchema(
                meal_name="Error Recipe",
                meal_type="breakfast",
                ingredients=["ingredient"],
                instructions=["instruction"]
            )
            
            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.add_recipe(test_user.id, recipe_data)
            
            assert "Database error" in str(exc_info.value)
            assert mock_session.add.called
            assert mock_session.commit.called

    class TestUpdateRecipe:
        """Tests for update_recipe method."""

        @pytest.mark.asyncio
        async def test_update_recipe(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test updating an existing recipe."""
            recipe_id = test_recipes[0].id
            update_data = RecipeUpdateSchema(
                meal_name="Updated Recipe Name",
                meal_type="dinner",
                ingredients=["updated ingredient 1", "updated ingredient 2"],
                instructions=["updated step 1", "updated step 2"]
            )
            
            updated_recipe = await recipe_manager.update_recipe(recipe_id, test_user.id, update_data)
            
            assert updated_recipe is not None
            assert updated_recipe.meal_name == "Updated Recipe Name"
            assert updated_recipe.meal_type == "dinner"
            
            await db_session.refresh(updated_recipe)
            assert updated_recipe.meal_name == "Updated Recipe Name"
            assert updated_recipe.meal_type == "dinner"
            assert json.loads(updated_recipe.ingredients) == ["updated ingredient 1", "updated ingredient 2"]
            assert json.loads(updated_recipe.instructions) == ["updated step 1", "updated step 2"]

        @pytest.mark.asyncio
        async def test_update_recipe_partial(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test partial update of a recipe (only some fields)."""
            recipe_id = test_recipes[1].id
            original_meal_type = test_recipes[1].meal_type
            original_ingredients = json.loads(test_recipes[1].ingredients)
            original_instructions = json.loads(test_recipes[1].instructions)
            
            update_data = RecipeUpdateSchema(
                meal_name="Partially Updated Recipe",
                meal_type=None,
                ingredients=None,
                instructions=None
            )
            
            updated_recipe = await recipe_manager.update_recipe(recipe_id, test_user.id, update_data)
            
            assert updated_recipe is not None
            assert updated_recipe.meal_name == "Partially Updated Recipe"
            assert updated_recipe.meal_type == original_meal_type
            
            await db_session.refresh(updated_recipe)
            assert updated_recipe.meal_name == "Partially Updated Recipe"
            assert updated_recipe.meal_type == original_meal_type
            assert json.loads(updated_recipe.ingredients) == original_ingredients
            assert json.loads(updated_recipe.instructions) == original_instructions

        @pytest.mark.asyncio
        async def test_update_recipe_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test updating a recipe that doesn't exist."""
            update_data = RecipeUpdateSchema(
                meal_name="This Won't Update",
                meal_type="dinner",
                ingredients=["ingredient"],
                instructions=["instruction"]
            )
            
            result = await recipe_manager.update_recipe(999, test_user.id, update_data)
            
            assert result is None

        @pytest.mark.asyncio
        async def test_update_recipe_empty_lists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test updating a recipe with empty lists."""
            recipe_id = test_recipes[0].id
            update_data = RecipeUpdateSchema(
                ingredients=[],
                instructions=[]
            )
            
            updated_recipe = await recipe_manager.update_recipe(recipe_id, test_user.id, update_data)
            
            assert updated_recipe is not None
            await db_session.refresh(updated_recipe)
            assert json.loads(updated_recipe.ingredients) == []
            assert json.loads(updated_recipe.instructions) == []

        @pytest.mark.asyncio
        async def test_update_recipe_database_error(self, test_user: TestUser) -> None:
            """Test handling database error when updating a recipe."""
            mock_session = AsyncMock()
            
            mock_recipe = TestRecipe(
                id=1,
                user_id=test_user.id,
                meal_name="Original Recipe",
                meal_type="breakfast",
                ingredients=json.dumps(["ingredient"]),
                instructions=json.dumps(["instruction"])
            )
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=mock_recipe)
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            mock_session.refresh = MagicMock()
            
            recipe_manager = RecipeManager(mock_session)
            
            update_data = RecipeUpdateSchema(
                meal_name="Error Recipe",
                meal_type="breakfast",
                ingredients=["ingredient"],
                instructions=["instruction"]
            )
            
            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.update_recipe(1, test_user.id, update_data)
            
            assert "Database error" in str(exc_info.value)
            assert mock_session.execute.called
            assert mock_session.commit.called

    class TestDeleteRecipe:
        """Tests for delete_recipe method."""

        @pytest.mark.asyncio
        async def test_delete_recipe(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test deleting a recipe."""
            recipe_id = test_recipes[0].id
            
            delete_result = await recipe_manager.delete_recipe(recipe_id, test_user.id)
            assert delete_result is True
            
            query = select(TestRecipe).filter_by(id=recipe_id)
            db_result = await db_session.execute(query)
            recipe = db_result.scalar_one_or_none()
            assert recipe is None

        @pytest.mark.asyncio
        async def test_delete_recipe_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test deleting a recipe that doesn't exist."""
            result = await recipe_manager.delete_recipe(999, test_user.id)
            
            assert result is False

        @pytest.mark.asyncio
        async def test_delete_recipe_wrong_user(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe],
            db_session: AsyncSession
        ) -> None:
            """Test deleting a recipe with wrong user ID."""
            recipe_id = test_recipes[0].id
            
            other_user = TestUser(
                user_name="other_user",
                email="other@example.com",
                hash="hashedpassword"
            )
            db_session.add(other_user)
            await db_session.commit()
            await db_session.refresh(other_user)
            
            result = await recipe_manager.delete_recipe(recipe_id, other_user.id)
            
            assert result is False
            
            query = select(TestRecipe).filter_by(id=recipe_id)
            db_result = await db_session.execute(query)
            recipe = db_result.scalar_one_or_none()
            assert recipe is not None

        @pytest.mark.asyncio
        async def test_delete_recipe_database_error(self, test_user: TestUser) -> None:
            """Test handling database error when deleting a recipe."""
            mock_session = AsyncMock()
            mock_recipe = MagicMock()

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=mock_recipe)
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_session.delete = AsyncMock(side_effect=SQLAlchemyError("Database error"))

            recipe_manager = RecipeManager(mock_session)

            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.delete_recipe(1, test_user.id)

            assert "Database error" in str(exc_info.value)
            assert mock_session.execute.called
            assert mock_session.delete.called
            
    class TestGetIngredientsByMealName:
        """Tests for get_ingredients_by_meal_name method."""

        @pytest.mark.asyncio
        async def test_get_ingredients_by_meal_name(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            test_recipes: list[TestRecipe]
        ) -> None:
            """Test retrieving ingredients for a recipe by meal name."""
            ingredients = await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Test Breakfast")
            
            assert ingredients is not None
            assert isinstance(ingredients, list)
            assert "eggs" in ingredients
            assert "bread" in ingredients
            assert "butter" in ingredients

        @pytest.mark.asyncio
        async def test_get_ingredients_by_meal_name_not_exists(
            self, recipe_manager: RecipeManager,
            test_user: TestUser
        ) -> None:
            """Test retrieving ingredients for a nonexistent recipe."""
            ingredients = await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Nonexistent Recipe")
            
            assert ingredients is None

        @pytest.mark.asyncio
        async def test_get_ingredients_by_meal_name_invalid_json(
            self, recipe_manager: RecipeManager,
            test_user: TestUser,
            db_session: AsyncSession
        ) -> None:
            """Test retrieving ingredients when JSON is invalid."""
            recipe = TestRecipe(
                user_id=test_user.id,
                meal_name="Invalid JSON Recipe",
                meal_type="breakfast",
                ingredients="invalid json",
                instructions=json.dumps(["step 1", "step 2"])
            )
            db_session.add(recipe)
            await db_session.commit()
            await db_session.refresh(recipe)
            
            with pytest.raises(json.JSONDecodeError):
                await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Invalid JSON Recipe")

        @pytest.mark.asyncio
        async def test_get_ingredients_by_meal_name_database_error(self, test_user: TestUser) -> None:
            """Test handling database error when getting ingredients by meal name."""
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            
            recipe_manager = RecipeManager(mock_session)
            
            with pytest.raises(SQLAlchemyError) as exc_info:
                await recipe_manager.get_ingredients_by_meal_name(test_user.id, "Test Recipe")
            
            assert "Database error" in str(exc_info.value)
            assert mock_session.execute.called
