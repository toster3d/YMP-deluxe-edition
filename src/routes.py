import logging
from datetime import date as date_type
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from jwt_utils import oauth2_scheme, verify_jwt
from resources.auth_resource import AuthResource, LogoutResource, RegisterResource
from resources.plan_resource import (
    ChooseMealResource,
    ScheduleResource,
    ScheduleResponse,
)
from resources.pydantic_schemas import (
    DateRangeSchema,
    PlanSchema,
    RecipeSchema,
    RecipeUpdateSchema,
    RegisterSchema,
    ShoppingListRangeResponse,
    ShoppingListResponse,
    TokenResponse,
)
from resources.recipe_resource import RecipeListResource, RecipeResource
from resources.shopping_list_resource import ShoppingListResource

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)



async def verify_token(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        payload = verify_jwt(token)
        return payload  
    except HTTPException as e:
        raise e

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
    """Login using OAuth2 credentials."""
    try:
        result = await auth_resource.login_with_form(form_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

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
    """Register new user."""
    return await register_resource.post(register_data)

@router.post(
    "/auth/logout",
    tags=["auth"],
    description="Logout user and invalidate token",
    response_model=dict[str, str]
)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    logout_resource: Annotated[LogoutResource, Depends()]
) -> dict[str, str]:
    """Logout user and invalidate their token."""
    return await logout_resource.post(token)


@router.get(
    "/recipe",
    tags=["recipes"],
    description="Get all recipes for authenticated user",
    response_model=dict[str, list[RecipeUpdateSchema]],
    dependencies=[Depends(verify_token)]
)
async def get_recipes(
    recipe_list_resource: Annotated[RecipeListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, list[RecipeSchema]]:
    """Get all recipes for authenticated user."""
    return await recipe_list_resource.get(user_id=int(current_user["sub"]))

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
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, Any]:
    """Create a new recipe."""
    return await recipe_list_resource.post(
        recipe_data=recipe_data,
        user_id=int(current_user["sub"])
    )

@router.get(
    "/recipe/{recipe_id}",
    tags=["recipes"],
    description="Get specific recipe by ID",
    response_model=RecipeUpdateSchema,
    dependencies=[Depends(verify_token)]
)
async def get_recipe(
    recipe_id: int,
    recipe_resource: Annotated[RecipeResource, Depends()],
    token: dict[str, Any] = Depends(verify_token)
) -> RecipeSchema:
    """Get recipe by ID."""
    user_id = int(token['sub'])
    return await recipe_resource.get(recipe_id, user_id)

@router.patch(
    "/recipe/{recipe_id}",
    tags=["recipes"],
    description="Update specific recipe",
    response_model=RecipeUpdateSchema,
    dependencies=[Depends(verify_token)]
)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdateSchema,
    recipe_resource: Annotated[RecipeResource, Depends()],
    token: dict[str, Any] = Depends(verify_token)
) -> RecipeUpdateSchema:
    """Update recipe by ID."""
    user_id = int(token['sub'])
    return await recipe_resource.patch(recipe_id, recipe_data, user_id)

@router.delete(
    "/recipe/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["recipes"],
    description="Delete specific recipe",
    dependencies=[Depends(verify_token)]
)
async def delete_recipe(
    recipe_id: int,
    recipe_resource: Annotated[RecipeResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> None:
    """Delete recipe by ID."""
    await recipe_resource.delete(
        recipe_id=recipe_id,
        user_id=int(current_user["sub"])
    )

@router.get(
    "/meal_plan",
    tags=["meal_plans"],
    description="Get meal plan options",
    response_model=dict[str, list[dict[str, Any]]],
    dependencies=[Depends(verify_token)]
)
async def choose_meal(
    choose_meal_resource: Annotated[ChooseMealResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, list[dict[str, Any]]]:
    """
    Get meal plan options endpoint.
    
    Returns:
        dict: Available recipes for meal planning
    """
    return await choose_meal_resource.get(user_id=int(current_user["sub"]))

@router.post(
    "/meal_plan",
    status_code=status.HTTP_201_CREATED,
    tags=["meal_plans"],
    description="Create new meal plan",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_token)]
)
async def create_meal_plan(
    plan_data: PlanSchema,
    choose_meal_resource: Annotated[ChooseMealResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, Any]:
    """
    Create meal plan endpoint.
    
    Returns:
        dict: Created meal plan details
    """
    return await choose_meal_resource.post(
        user_id=int(current_user["sub"]),
        plan_data=plan_data
    )

@router.get(
    "/schedule",
    tags=["schedules"],
    description="Get user's schedule",
    response_model=ScheduleResponse,
    dependencies=[Depends(verify_token)]
)
async def get_schedule(
    schedule_resource: Annotated[ScheduleResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token),
    date: str | None = Query(None, description="Date in ISO format (YYYY-MM-DD)")
) -> ScheduleResponse:
    """Get schedule endpoint."""
    try:
        if date:
            schedule_date = date_type.fromisoformat(date)
        else:
            schedule_date = date_type.today()
            
        return await schedule_resource.get(
            user_id=int(current_user["sub"]),
            date_param=schedule_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD format: {str(e)}"
        )

@router.get(
    "/shopping_list",
    tags=["shopping_lists"],
    description="Get shopping list for today",
    response_model=ShoppingListResponse,
    responses={
        404: {"description": "No meal plan found for today"},
        500: {"description": "Internal server error"}
    },
    dependencies=[Depends(verify_token)]
)
async def get_shopping_list(
    shopping_list_resource: Annotated[ShoppingListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> ShoppingListResponse:
    """Get shopping list for today's meal plan."""
    return await shopping_list_resource.get(user_id=int(current_user["sub"]))

@router.post(
    "/shopping_list",
    tags=["shopping_lists"],
    description="Get shopping list for date range",
    response_model=ShoppingListRangeResponse,
    dependencies=[Depends(verify_token)]
)
async def get_shopping_list_for_range(
    date_range: DateRangeSchema,
    shopping_list_resource: Annotated[ShoppingListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> ShoppingListRangeResponse:
    """Get shopping list for specified date range."""
    return await shopping_list_resource.post(
        user_id=int(current_user["sub"]),
        date_range_data=date_range
    )

@router.get(
    "/health", 
    status_code=status.HTTP_200_OK, 
    response_model=dict[str, str]
)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        dict: Status of the application
    """
    return {"status": "healthy"}
