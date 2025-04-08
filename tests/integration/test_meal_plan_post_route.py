import json
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models.models_db_test import TestRecipe, TestUser, TestUserPlan


@pytest.mark.asyncio
class TestMealPlanPostRoute:
    """Tests for POST /meal_plan endpoint."""

    @pytest.fixture
    async def test_recipe(
        self,
        db_session: AsyncSession,
        create_test_user: TestUser
    ) -> TestRecipe:
        """Create a test recipe for the user."""
        recipe = TestRecipe(
            user_id=create_test_user.id,
            meal_name="Spaghetti Aglio e Olio",
            meal_type="dinner",
            ingredients=json.dumps(["Spaghetti", "Garlic", "Olive oil", "Parsley", "Salt", "Pepper"]),
            instructions=json.dumps(["Cook the pasta", "Sauté garlic in olive oil", "Mix with pasta"])
        )
        db_session.add(recipe)
        await db_session.commit()
        await db_session.refresh(recipe)
        return recipe

    @pytest.fixture
    async def existing_plan(
        self,
        db_session: AsyncSession,
        create_test_user: TestUser
    ) -> TestUserPlan:
        """Create an existing meal plan."""
        plan = TestUserPlan(
            user_id=create_test_user.id,
            date=date.today(),
            breakfast="Oatmeal",
            lunch="Tuna sandwich",
            dinner=None,
            dessert="Pudding"
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        return plan

    class TestSuccessScenarios:
        """Tests for successful meal plan creation scenarios."""

        async def test_create_meal_plan_success(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe: TestRecipe,
            db_session: AsyncSession,
        ) -> None:
            """Test successful creation of a new meal plan."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            data = response.json()
            assert data["message"] == "Meal plan updated successfully!"
            assert data["meal_type"] == "dinner"
            assert data["recipe_name"] == test_recipe.meal_name
            assert data["recipe_id"] == test_recipe.id
            assert data["date"] == today.isoformat()
            
            result = await db_session.execute(
                select(TestUserPlan).filter(
                    TestUserPlan.user_id == test_recipe.user_id,
                    TestUserPlan.date == today
                )
            )
            plan = result.scalar_one_or_none()
            assert plan is not None
            assert plan.dinner == test_recipe.meal_name
            assert plan.breakfast is None
            assert plan.lunch is None
            assert plan.dessert is None

        async def test_update_existing_meal_plan(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe: TestRecipe,
            existing_plan: TestUserPlan,
            db_session: AsyncSession,
        ) -> None:
            """Test updating an existing meal plan."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            data = response.json()
            assert data["message"] == "Meal plan updated successfully!"
            assert data["meal_type"] == "dinner"
            
            await db_session.refresh(existing_plan)
            result = await db_session.execute(
                select(TestUserPlan).filter(
                    TestUserPlan.user_id == test_recipe.user_id,
                    TestUserPlan.date == today
                )
            )
            plan = result.scalar_one_or_none()
            assert plan is not None
            assert plan.dinner == test_recipe.meal_name
            assert plan.breakfast == "Oatmeal"
            assert plan.lunch == "Tuna sandwich"
            assert plan.dessert == "Pudding"

        async def test_create_meal_plan_future_date(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe: TestRecipe,
            db_session: AsyncSession,
        ) -> None:
            """Test creating a meal plan for a future date."""
            future_date = date.today() + timedelta(days=7)
            payload = {
                "selected_date": future_date.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            result = await db_session.execute(
                select(TestUserPlan).filter(
                    TestUserPlan.user_id == test_recipe.user_id,
                    TestUserPlan.date == future_date
                )
            )
            plan = result.scalar_one_or_none()
            assert plan is not None
            assert plan.dinner == test_recipe.meal_name

    class TestErrorScenarios:
        """Tests for error scenarios."""

        async def test_create_meal_plan_nonexistent_recipe(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
        ) -> None:
            """Test attempting to create a plan with a nonexistent recipe."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": 999999,
                "meal_type": "breakfast"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "Recipe with id 999999 not found" in data["detail"]

        async def test_create_meal_plan_invalid_meal_type(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe: TestRecipe,
        ) -> None:
            """Test attempting to create a plan with an invalid meal type."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "invalid_type"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert "input should be" in data["detail"][0]["msg"].lower()

        async def test_create_meal_plan_invalid_date_format(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
            test_recipe: TestRecipe,
        ) -> None:
            """Test attempting to create a plan with an invalid date format."""
            payload = {
                "selected_date": "05-03-2025",
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert len(data["detail"]) > 0
            assert any("selected_date" in str(error.get("loc", [])) for error in data["detail"])

        async def test_create_meal_plan_missing_fields(
            self,
            async_client: AsyncClient,
            auth_headers: dict[str, str],
        ) -> None:
            """Test attempting to create a plan with missing required fields."""
            payload: dict[str, Any] = {}
            
            response = await async_client.post(
                "/meal_plan",
                headers=auth_headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert len(data["detail"]) > 0

    class TestAuthorizationScenarios:
        """Tests for authorization scenarios."""

        async def test_create_meal_plan_unauthorized(
            self,
            async_client: AsyncClient,
            test_recipe: TestRecipe,
        ) -> None:
            """Test attempting to create a plan without authorization."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            
            response = await async_client.post(
                "/meal_plan",
                json=payload
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        async def test_create_meal_plan_invalid_token(
            self,
            async_client: AsyncClient,
            test_recipe: TestRecipe,
        ) -> None:
            """Test attempting to create a plan with an invalid token."""
            today = date.today()
            payload = {
                "selected_date": today.isoformat(),
                "recipe_id": test_recipe.id,
                "meal_type": "dinner"
            }
            headers = {"Authorization": "Bearer invalid.token"}
            
            response = await async_client.post(
                "/meal_plan",
                headers=headers,
                json=payload
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED