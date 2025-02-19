# from datetime import date

# import pytest
# from fastapi import status
# from httpx import AsyncClient


# @pytest.mark.asyncio
# async def test_get_meal_plan_options(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test getting meal plan options."""
#     response = await async_client.get(
#         "/meal_plan",
#         headers=auth_headers
#     )
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert "recipes" in data
#     assert isinstance(data["recipes"], list)

# @pytest.mark.asyncio
# async def test_create_meal_plan(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test creating a meal plan."""
#     today = date.today()
#     plan_data = {
#         "date": today.isoformat(),
#         "recipe_id": 1,
#         "meal_type": "lunch"
#     }
    
#     response = await async_client.post(
#         "/meal_plan",
#         headers=auth_headers,
#         json=plan_data
#     )
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
#     assert "id" in data
#     assert data["date"] == plan_data["date"]

# @pytest.mark.asyncio
# async def test_get_schedule(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test getting schedule."""
#     response = await async_client.get(
#         "/schedule",
#         headers=auth_headers
#     )
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert "schedule" in data 