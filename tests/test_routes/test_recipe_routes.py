# import pytest
# from fastapi import status
# from httpx import AsyncClient


# @pytest.mark.asyncio
# async def test_get_recipes(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test getting all recipes."""
#     response = await async_client.get(
#         "/recipe",
#         headers=auth_headers
#     )
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert "recipes" in data
#     assert isinstance(data["recipes"], list)

# @pytest.mark.asyncio
# async def test_create_recipe(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test creating a new recipe."""
#     recipe_data = {
#         "name": "Test Recipe",
#         "description": "Test Description",
#         "ingredients": [
#             {"name": "Test Ingredient", "amount": 1, "unit": "piece"}
#         ],
#         "instructions": ["Step 1", "Step 2"]
#     }
    
#     response = await async_client.post(
#         "/recipe",
#         headers=auth_headers,
#         json=recipe_data
#     )
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
#     assert "id" in data
#     assert data["name"] == recipe_data["name"]

# @pytest.mark.asyncio
# async def test_get_recipe(
#     async_client: AsyncClient,
#     auth_headers: dict[str, str]
# ) -> None:
#     """Test getting a specific recipe."""
#     # First create a recipe
#     recipe_data = {
#         "name": "Test Recipe",
#         "description": "Test Description",
#         "ingredients": [
#             {"name": "Test Ingredient", "amount": 1, "unit": "piece"}
#         ],
#         "instructions": ["Step 1", "Step 2"]
#     }
    
#     create_response = await async_client.post(
#         "/recipe",
#         headers=auth_headers,
#         json=recipe_data
#     )
#     recipe_id = create_response.json()["id"]
    
#     # Then get it
#     response = await async_client.get(
#         f"/recipe/{recipe_id}",
#         headers=auth_headers
#     )
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["id"] == recipe_id
#     assert data["name"] == recipe_data["name"] 