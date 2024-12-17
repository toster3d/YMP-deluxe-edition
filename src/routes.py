from http.client import HTTPException
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import oauth2_scheme
from jwt_utils import verify_jwt  # Importuj funkcję weryfikującą token
from resources.auth_resource import AuthResource, LogoutResource, RegisterResource
from resources.plan_resource import ChooseMealResource, ScheduleResource
from resources.pydantic_schemas import (
    PlanSchema,
    RecipeSchema,
    RecipeUpdateSchema,
    RegisterSchema,
    TokenResponse,
)
from resources.recipe_resource import RecipeListResource, RecipeResource
from resources.shopping_list_resource import ShoppingListResource
from services.recipe_manager import RecipeDict

# Create router with prefix and tags
router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)



async def verify_token(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        payload = verify_jwt(token)
        return payload  # Możesz zwrócić payload, jeśli potrzebujesz
    except HTTPException as e:
        raise e  # Przekaż wyjątek dalej

# Auth routes
@router.post(
    "/auth/login",
    tags=["auth"],
    description="Login endpoint using OAuth2",
    response_model=TokenResponse
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_resource: Annotated[AuthResource, Depends()]
) -> TokenResponse:
    """Login endpoint using OAuth2."""
    return await auth_resource.login_with_form(form_data)

@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    description="Register new user",
    response_model=dict[str, str]
)
async def register(
    register_data: RegisterSchema,
    register_resource: Annotated[RegisterResource, Depends()]
) -> dict[str, str]:
    """
    Register endpoint.
    
    Args:
        register_data: User registration data
        register_resource: Registration resource
        
    Returns:
        dict: Registration confirmation message
    """
    return await register_resource.post(register_data)

@router.post(
    "/auth/logout",
    tags=["auth"],
    description="Logout user and invalidate token",
    response_model=dict[str, str],
    dependencies=[Depends(verify_token)]
)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    logout_resource: Annotated[LogoutResource, Depends()]
) -> dict[str, str]:
    """
    Logout endpoint.
    
    Args:
        token: JWT token to invalidate
        logout_resource: Logout resource
        
    Returns:
        dict: Logout confirmation message
    """
    return await logout_resource.post(token)

# Recipe routes
@router.get(
    "/recipe",
    tags=["recipes"],
    description="Get all recipes for authenticated user",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_token)]
)
async def get_recipes(
    recipe_list_resource: Annotated[RecipeListResource, Depends()],
    token: str = Depends(verify_token)
) -> dict[str, Any]:
    """Get all recipes endpoint."""
    return await recipe_list_resource.get()

@router.post(
    "/recipe",
    status_code=status.HTTP_201_CREATED,
    tags=["recipes"],
    description="Create new recipe",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_token)]
)
async def create_recipe(
    recipe_data: RecipeSchema,
    recipe_list_resource: Annotated[RecipeListResource, Depends()],
    token: str = Depends(verify_token)
) -> dict[str, Any]:
    """
    Create recipe endpoint.
    
    Args:
        recipe_data: Recipe data
        recipe_list_resource: Recipe list resource
        
    Returns:
        dict: Created recipe
    """
    return await recipe_list_resource.post(recipe_data)

@router.get(
    "/recipe/{recipe_id}",
    tags=["recipes"],
    description="Get specific recipe by ID",
    response_model=RecipeDict,
    dependencies=[Depends(verify_token)]
)
async def get_recipe(
    recipe_id: int,
    recipe_resource: Annotated[RecipeResource, Depends()],
    token: str = Depends(verify_token)
) -> RecipeDict:
    return await recipe_resource.get(recipe_id, token)

@router.patch(
    "/recipe/{recipe_id}",
    tags=["recipes"],
    description="Update specific recipe",
    response_model=RecipeDict,
    dependencies=[Depends(verify_token)]
)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdateSchema,
    recipe_resource: Annotated[RecipeResource, Depends()],
    token: str = Depends(verify_token)
) -> RecipeDict:
    result: RecipeDict | None = await recipe_resource.patch(recipe_id, recipe_data, token)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
    return result

@router.delete(
    "/recipe/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["recipes"],
    description="Delete specific recipe",
    dependencies=[Depends(verify_token)]
)
async def delete_recipe(
    recipe_id: int,
    recipe_resource: RecipeResource = Depends(),
    token: str = Depends(verify_token)
) -> None:
    """
    Delete recipe endpoint.
    
    Args:
        recipe_id: Recipe ID
        recipe_resource: Recipe resource
    """
    await recipe_resource.delete(recipe_id)

# Meal plan routes
@router.get(
    "/meal_plan",
    tags=["meal_plans"],
    description="Get meal plan options",
    dependencies=[Depends(verify_token)]
)
async def choose_meal(
    choose_meal_resource: ChooseMealResource = Depends()
) -> JSONResponse:
    """
    Get meal plan options endpoint.
    
    Args:
        choose_meal_resource: Choose meal resource
        
    Returns:
        JSON response with meal plan options
    """
    return await choose_meal_resource.get()

@router.post(
    "/meal_plan",
    status_code=status.HTTP_201_CREATED,
    tags=["meal_plans"],
    description="Create new meal plan",
    dependencies=[Depends(verify_token)]
)
async def create_meal_plan(
    plan_data: PlanSchema,
    choose_meal_resource: ChooseMealResource = Depends()
) -> JSONResponse:
    """
    Create meal plan endpoint.
    
    Args:
        plan_data: Meal plan data
        choose_meal_resource: Choose meal resource
        
    Returns:
        JSON response with created meal plan
    """
    return await choose_meal_resource.post(plan_data)

# Schedule routes
@router.get(
    "/schedule",
    tags=["schedules"],
    description="Get user's schedule",
    dependencies=[Depends(verify_token)]    
)
async def get_schedule(
    schedule_resource: ScheduleResource = Depends()
) -> JSONResponse:
    """
    Get schedule endpoint.
    
    Args:
        schedule_resource: Schedule resource
        
    Returns:
        JSON response with user's schedule
    """
    return await schedule_resource.get()

# Shopping list routes
@router.get(
    "/shopping_list",
    tags=["shopping_lists"],
    description="Get shopping list for meal plan",
    dependencies=[Depends(verify_token)]
)
async def get_shopping_list(
    shopping_list_resource: ShoppingListResource = Depends()
) -> JSONResponse:
    """
    Get shopping list endpoint.
    
    Args:
        shopping_list_resource: Shopping list resource
        
    Returns:
        JSON response with shopping list
    """
    return await shopping_list_resource.get()
