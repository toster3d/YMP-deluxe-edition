import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.user_plan_manager import SqlAlchemyUserPlanManager
from tests.test_models.models_db_test import TestRecipe, TestUser, TestUserPlan


@pytest.fixture
async def user_plan_manager(db_session: AsyncSession) -> SqlAlchemyUserPlanManager:
    return SqlAlchemyUserPlanManager(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> TestUser:
    user = TestUser(
        user_name="plan_manager_test_user",
        email="plan_manager_test@example.com",
        hash="hashedpassword"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_recipes(db_session: AsyncSession, test_user: TestUser) -> list[TestRecipe]:
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
            instructions=json.dumps(["cook chicken", "prepare rice", "serve"])
        ),
        TestRecipe(
            user_id=test_user.id,
            meal_name="Test Dinner",
            meal_type="dinner",
            ingredients=json.dumps(["pasta", "tomato sauce", "cheese"]),
            instructions=json.dumps(["boil pasta", "heat sauce", "serve"])
        ),
        TestRecipe(
            user_id=test_user.id,
            meal_name="Test Dessert",
            meal_type="dessert",
            ingredients=json.dumps(["flour", "sugar", "eggs", "milk"]),
            instructions=json.dumps(["mix ingredients", "bake", "serve"])
        )
    ]
    
    for recipe in recipes:
        db_session.add(recipe)
    
    await db_session.commit()
    
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    return recipes


@pytest.fixture
async def test_user_plan(db_session: AsyncSession, test_user: TestUser) -> TestUserPlan:
    today = date.today()
    plan = TestUserPlan(
        user_id=test_user.id,
        date=today,
        breakfast="Test Breakfast",
        lunch="Test Lunch",
        dinner=None,
        dessert=None
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


class TestGetPlans:
    
    @pytest.mark.asyncio
    async def test_get_plans_existing(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_user_plan: TestUserPlan
    ) -> None:
        today = date.today()
        result = await user_plan_manager.get_plans(test_user.id, today)
        
        assert isinstance(result, dict)
        assert result["user_id"] == test_user.id
        assert result["date"] == today
        assert result["breakfast"] == "Test Breakfast"
        assert result["lunch"] == "Test Lunch"
        assert result["dinner"] is None
        assert result["dessert"] is None

    @pytest.mark.asyncio
    async def test_get_plans_nonexistent(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser
    ) -> None:
        tomorrow = date.today() + timedelta(days=1)
        result = await user_plan_manager.get_plans(test_user.id, tomorrow)
        
        assert isinstance(result, dict)
        assert result["user_id"] == test_user.id
        assert result["date"] == tomorrow
        assert result["breakfast"] is None
        assert result["lunch"] is None
        assert result["dinner"] is None
        assert result["dessert"] is None
        
    @pytest.mark.asyncio
    async def test_get_plans_database_error(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        db_session: AsyncSession
    ) -> None:
        today = date.today()
        
        with patch.object(db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                await user_plan_manager.get_plans(test_user.id, today)
            
            assert "Database error" in str(exc_info.value)


class TestCreateOrUpdatePlan:
    
    @pytest.mark.asyncio
    async def test_create_plan(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_recipes: list[TestRecipe],
        db_session: AsyncSession
    ) -> None:
        tomorrow = date.today() + timedelta(days=1)
        breakfast_recipe = next(r for r in test_recipes if r.meal_type == "breakfast")
        
        with patch.object(db_session, 'begin', return_value=AsyncMock()):
            result = await user_plan_manager.create_or_update_plan(
                test_user.id, 
                tomorrow, 
                breakfast_recipe.id, 
                "breakfast"
            )
        
        assert isinstance(result, dict)
        assert result["meal_type"] == "breakfast"
        assert result["recipe_name"] == breakfast_recipe.meal_name
        assert result["recipe_id"] == breakfast_recipe.id
        assert result["date"] == tomorrow.isoformat()
        
        query = select(TestUserPlan).filter_by(user_id=test_user.id, date=tomorrow)
        db_result = await db_session.execute(query)
        plan = db_result.scalar_one_or_none()
        
        assert plan is not None
        assert plan.breakfast == breakfast_recipe.meal_name
        assert plan.lunch is None
        assert plan.dinner is None
        assert plan.dessert is None

    @pytest.mark.asyncio
    async def test_update_plan(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_recipes: list[TestRecipe],
        test_user_plan: TestUserPlan,
        db_session: AsyncSession
    ) -> None:
        today = date.today()
        dinner_recipe = next(r for r in test_recipes if r.meal_type == "dinner")
        
        with patch.object(db_session, 'begin', return_value=AsyncMock()):
            result = await user_plan_manager.create_or_update_plan(
                test_user.id, 
                today, 
                dinner_recipe.id, 
                "dinner"
            )
        
        assert isinstance(result, dict)
        assert result["meal_type"] == "dinner"
        assert result["recipe_name"] == dinner_recipe.meal_name
        assert result["recipe_id"] == dinner_recipe.id
        assert result["date"] == today.isoformat()
        
        await db_session.refresh(test_user_plan)
        assert test_user_plan.breakfast == "Test Breakfast"
        assert test_user_plan.lunch == "Test Lunch"
        assert test_user_plan.dinner == dinner_recipe.meal_name
        assert test_user_plan.dessert is None
        
    @pytest.mark.asyncio
    async def test_create_or_update_plan_nonexistent_recipe(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        db_session: AsyncSession
    ) -> None:
        today = date.today()
        nonexistent_recipe_id = 99999
        
        with patch.object(db_session, 'begin', return_value=AsyncMock()):
            with pytest.raises(ValueError) as exc_info:
                await user_plan_manager.create_or_update_plan(
                    test_user.id,
                    today,
                    nonexistent_recipe_id,
                    "breakfast"
                )
        
        assert f"Recipe with id {nonexistent_recipe_id} not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_or_update_plan_invalid_meal_type(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_recipes: list[TestRecipe],
        db_session: AsyncSession
    ) -> None:
        today = date.today()
        recipe = test_recipes[0]
        invalid_meal_type = "invalid_type"
        
        with patch.object(db_session, 'begin', return_value=AsyncMock()):
            with pytest.raises(ValueError) as exc_info:
                await user_plan_manager.create_or_update_plan(
                    test_user.id,
                    today,
                    recipe.id,
                    invalid_meal_type
                )
        
        assert f"Invalid meal_type: {invalid_meal_type}" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_create_or_update_plan_database_error(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_recipes: list[TestRecipe],
        db_session: AsyncSession
    ) -> None:
        today = date.today()
        recipe = test_recipes[0]
        
        with patch.object(db_session, 'begin', return_value=AsyncMock()), \
             patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                await user_plan_manager.create_or_update_plan(
                    test_user.id,
                    today,
                    recipe.id,
                    "breakfast"
                )
            
            assert "Database error" in str(exc_info.value)


class TestGetUserRecipes:
    
    @pytest.mark.asyncio
    async def test_get_user_recipes(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        test_recipes: list[TestRecipe]
    ) -> None:
        result = await user_plan_manager.get_user_recipes(test_user.id)
        
        assert isinstance(result, list)
        assert len(result) == 4
        
        for recipe in result:
            assert "id" in recipe
            assert "name" in recipe
            assert "meal_type" in recipe
            assert recipe["meal_type"] in ["breakfast", "lunch", "dinner", "dessert"]
        
        recipe_names = [recipe["name"] for recipe in result]
        expected_names = ["Test Breakfast", "Test Lunch", "Test Dinner", "Test Dessert"]
        assert set(recipe_names) == set(expected_names)

    @pytest.mark.asyncio
    async def test_get_user_recipes_no_recipes(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        db_session: AsyncSession
    ) -> None:
        user = TestUser(
            user_name="user_without_recipes",
            email="no_recipes@example.com",
            hash="hashedpassword"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        result = await user_plan_manager.get_user_recipes(user.id)
        
        assert isinstance(result, list)
        assert len(result) == 0
        
    @pytest.mark.asyncio
    async def test_get_user_recipes_database_error(
        self,
        user_plan_manager: SqlAlchemyUserPlanManager,
        test_user: TestUser,
        db_session: AsyncSession
    ) -> None:
        with patch.object(db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                await user_plan_manager.get_user_recipes(test_user.id)
            
            assert "Database error" in str(exc_info.value)
