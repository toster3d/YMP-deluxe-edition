from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
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
    """Login using OAuth2 credentials."""
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
    """Register new user."""
    return await register_resource.post(register_data)

@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    logout_resource: Annotated[LogoutResource, Depends()]
) -> dict[str, str]:
    return await logout_resource.post(token)

# Recipe routes
@router.get(
    "/recipe",
    tags=["recipes"],
    description="Get all recipes for authenticated user",
    response_model=dict[str, list[RecipeDict]],
    dependencies=[Depends(verify_token)]
)
async def get_recipes(
    recipe_list_resource: Annotated[RecipeListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, list[RecipeDict]]:
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
    response_model=RecipeDict,
    dependencies=[Depends(verify_token)]
)
async def get_recipe(
    recipe_id: int,
    recipe_resource: Annotated[RecipeResource, Depends()],
    token: dict[str, Any] = Depends(verify_token)
) -> RecipeDict:
    """Get recipe by ID."""
    user_id = int(token['sub'])
    return await recipe_resource.get(recipe_id, user_id)

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
    token: dict[str, Any] = Depends(verify_token)
) -> RecipeDict:
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

# Meal plan routes
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

# Schedule routes
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
    date_str: str | None = None
) -> ScheduleResponse:
    """
    Get schedule endpoint.
    
    Returns:
        ScheduleResponse: User's schedule for specified date
    """
    return await schedule_resource.get(
        user_id=int(current_user["sub"]),
        date_str=date_str
    )

# Shopping list routes
@router.get(
    "/shopping_list",
    tags=["shopping_lists"],
    description="Get shopping list for today",
    response_model=dict[str, list[str] | str],
    dependencies=[Depends(verify_token)]
)
async def get_shopping_list(
    shopping_list_resource: Annotated[ShoppingListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, list[str] | str]:
    """Get shopping list for today's meal plan."""
    return await shopping_list_resource.get(user_id=int(current_user["sub"]))

@router.post(
    "/shopping_list",
    tags=["shopping_lists"],
    description="Get shopping list for date range",
    response_model=dict[str, list[str] | str],
    dependencies=[Depends(verify_token)]
)
async def get_shopping_list_for_range(
    date_range: DateRangeSchema,
    shopping_list_resource: Annotated[ShoppingListResource, Depends()],
    current_user: dict[str, Any] = Depends(verify_token)
) -> dict[str, list[str] | str]:
    """Get shopping list for specified date range."""
    return await shopping_list_resource.post(
        user_id=int(current_user["sub"]),
        date_range_data=date_range
    )
