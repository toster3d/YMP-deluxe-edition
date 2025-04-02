import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from resources.pydantic_schemas import VALID_MEAL_TYPES
from test_models.models_db_test import TestRecipe, TestUser, TestUserPlan


@pytest.fixture
async def unique_user(db_session: AsyncSession) -> TestUser:
    """Fixture creating a unique user for tests."""
    user = TestUser(
        user_name=f"TestUser-{uuid.uuid4()}",
        hash="hashedpassword",
        email=f"test{uuid.uuid4()}@example.com"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_recipe(db_session: AsyncSession, unique_user: TestUser) -> TestRecipe:
    """Fixture creating a test recipe."""
    recipe = TestRecipe(
        user_id=unique_user.id,
        meal_name="Test Meal",
        meal_type="breakfast",
        ingredients="Test Ingredients",
        instructions="Test Instructions"
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest.fixture
async def test_user_plan(db_session: AsyncSession, unique_user: TestUser) -> TestUserPlan:
    """Fixture creating a test user plan."""
    today = date.today()
    user_plan = TestUserPlan(
        user_id=unique_user.id,
        date=today,
        breakfast="Scrambled eggs",
        lunch="Chicken with rice",
        dinner="Sandwich",
        dessert="Chocolate"
    )
    db_session.add(user_plan)
    await db_session.commit()
    await db_session.refresh(user_plan)
    return user_plan


class TestUserModel:
    """Tests for the TestUser model."""

    @pytest.mark.anyio
    async def test_create_user(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests creating a user in the database."""
        assert unique_user.id is not None
        assert "TestUser-" in unique_user.user_name
        assert "test" in unique_user.email
        
        user_from_db = await db_session.get(TestUser, unique_user.id)
        assert user_from_db is not None
        assert user_from_db.user_name == unique_user.user_name

    @pytest.mark.anyio
    async def test_user_email_unique_constraint(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests that user email must be unique."""
        duplicate_user = TestUser(
            user_name="Another User",
            hash="hashedpassword",
            email=unique_user.email
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.anyio
    async def test_user_cascade_delete_recipes(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests that deleting a user cascades to deleting their recipes."""
        recipe = TestRecipe(
            user_id=unique_user.id,
            meal_name="Test Recipe",
            meal_type="breakfast",
            ingredients="Test ingredients",
            instructions="Test instructions"
        )
        db_session.add(recipe)
        await db_session.commit()
        
        recipe_id = recipe.id
        
        await db_session.delete(unique_user)
        await db_session.commit()
        
        deleted_recipe = await db_session.get(TestRecipe, recipe_id)
        assert deleted_recipe is None

    def test_user_has_recipes(self) -> None:
        """Checks if the user has assigned recipes."""
        user = TestUser(user_name="TestUser", hash="hashedpassword", email="test@example.com")
        recipe1 = TestRecipe(
            user_id=user.id, 
            meal_name="Pizza", 
            meal_type="dinner", 
            ingredients="Dough, cheese, sauce", 
            instructions="Bake the pizza"
        )
        recipe2 = TestRecipe(
            user_id=user.id, 
            meal_name="Tiramisu", 
            meal_type="dessert", 
            ingredients="Mascarpone, coffee, ladyfingers", 
            instructions="Mix the ingredients"
        )

        user.recipes = [recipe1, recipe2]

        assert user is not None
        assert len(user.recipes) == 2
        assert {r.meal_name for r in user.recipes} == {"Pizza", "Tiramisu"}


class TestRecipeModel:
    """Tests for the TestRecipe model."""

    @pytest.mark.anyio
    async def test_create_recipe(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests adding a recipe and linking it to a user."""
        recipe = TestRecipe(
            user_id=unique_user.id,
            meal_name="Test Meal",
            meal_type=VALID_MEAL_TYPES[0],
            ingredients="Test Ingredients",
            instructions="Test Instructions"
        )
        db_session.add(recipe)
        await db_session.commit()
        await db_session.refresh(recipe)

        recipe_from_db = await db_session.get(
            TestRecipe, recipe.id, options=[selectinload(TestRecipe.user)]
        )

        assert recipe_from_db is not None
        assert recipe_from_db.user.id == unique_user.id
        assert recipe_from_db.meal_name == "Test Meal"
        assert recipe_from_db.meal_type == VALID_MEAL_TYPES[0]

    @pytest.mark.anyio
    async def test_recipe_requires_valid_meal_type(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests that recipes require a valid meal type from the enum."""
        with pytest.raises(Exception):
            invalid_recipe = TestRecipe(
                user_id=unique_user.id,
                meal_name="Invalid Recipe",
                meal_type="invalid_type",
                ingredients="Test Ingredients",
                instructions="Test Instructions"
            )
            db_session.add(invalid_recipe)
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.anyio
    async def test_recipe_user_relationship(self, db_session: AsyncSession, test_recipe: TestRecipe) -> None:
        """Tests the relationship between recipes and users."""
        recipe_with_user = await db_session.get(
            TestRecipe, test_recipe.id, options=[selectinload(TestRecipe.user)]
        )
        assert recipe_with_user is not None
        assert recipe_with_user.user is not None
        assert recipe_with_user.user.id == test_recipe.user_id
        
        user = await db_session.get(
            TestUser, test_recipe.user_id, options=[selectinload(TestUser.recipes)]
        )
        assert user is not None
        assert any(r.id == test_recipe.id for r in user.recipes)


class TestUserPlanModel:
    """Tests for the TestUserPlan model."""

    @pytest.mark.anyio
    async def test_create_user_plan(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests adding a user plan."""
        test_date = date(2025, 2, 20)
        user_plan = TestUserPlan(
            user_id=unique_user.id,
            date=test_date,
            breakfast="Scrambled eggs",
            lunch="Chicken with rice",
            dinner="Sandwich",
            dessert="Chocolate"
        )
        db_session.add(user_plan)
        await db_session.commit()
        await db_session.refresh(user_plan)

        assert user_plan.id is not None
        assert user_plan.user_id == unique_user.id
        assert user_plan.date == test_date
        assert user_plan.breakfast == "Scrambled eggs"
        assert user_plan.lunch == "Chicken with rice"
        assert user_plan.dinner == "Sandwich"
        assert user_plan.dessert == "Chocolate"

    @pytest.mark.anyio
    async def test_user_plan_nullable_fields(self, db_session: AsyncSession, unique_user: TestUser) -> None:
        """Tests that meal fields in user plan can be null."""
        test_date = date(2025, 2, 21)
        user_plan = TestUserPlan(
            user_id=unique_user.id,
            date=test_date,
            breakfast="Oatmeal",
            dinner="Pasta",
        )
        db_session.add(user_plan)
        await db_session.commit()
        await db_session.refresh(user_plan)

        assert user_plan.id is not None
        assert user_plan.breakfast == "Oatmeal"
        assert user_plan.lunch is None
        assert user_plan.dinner == "Pasta"
        assert user_plan.dessert is None

    @pytest.mark.anyio
    async def test_user_plan_user_relationship(self, db_session: AsyncSession, test_user_plan: TestUserPlan) -> None:
        """Tests the relationship between user plans and users."""
        plan_with_user = await db_session.get(
            TestUserPlan, test_user_plan.id, options=[selectinload(TestUserPlan.user)]
        )
        assert plan_with_user is not None
        assert plan_with_user.user is not None
        assert plan_with_user.user.id == test_user_plan.user_id
        
        user = await db_session.get(
            TestUser, test_user_plan.user_id, options=[selectinload(TestUser.user_plans)]
        )
        assert user is not None
        assert any(p.id == test_user_plan.id for p in user.user_plans)

    @pytest.mark.anyio
    async def test_user_plan_cascade_delete(self, db_session: AsyncSession, test_user_plan: TestUserPlan) -> None:
        """Tests that deleting a user cascades to deleting their plans."""
        plan_id = test_user_plan.id
        user_id = test_user_plan.user_id
        
        user = await db_session.get(TestUser, user_id)
        assert user is not None
        await db_session.delete(user)
        await db_session.commit()
        
        deleted_plan = await db_session.get(TestUserPlan, plan_id)
        assert deleted_plan is None
