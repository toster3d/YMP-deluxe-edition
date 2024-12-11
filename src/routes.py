from fastapi import APIRouter, Depends
from typing import Any

from resources.auth_resource import AuthResource, LogoutResource, RegisterResource
from resources.plan_resource import ChooseMealResource, ScheduleResource
from resources.recipe_resource import RecipeListResource, RecipeResource
from resources.shopping_list_resource import ShoppingListResource

router = APIRouter()

# Trasy dla autoryzacji
@router.post("/auth/login", response_model=dict)
async def login(auth_resource: AuthResource = Depends()) -> Any:
    return await auth_resource.post() 

@router.post("/auth/register", response_model=dict)
async def register(register_resource: RegisterResource = Depends()) -> Any:
    return await register_resource.post()

@router.post("/auth/logout", response_model=dict)
    async def logout(logout_resource: LogoutResource = Depends()) -> Any:
    return await logout_resource.post()

# Trasy dla przepisów
@router.get("/recipe", response_model=list)
async def get_recipes(recipe_list_resource: RecipeListResource = Depends()) -> Any:
    return await recipe_list_resource.get()

@router.post("/recipe", response_model=dict)
async def create_recipe(recipe_list_resource: RecipeListResource = Depends()) -> Any:
    return await recipe_list_resource.post()

@router.get("/recipe/{recipe_id}", response_model=dict)
    async def get_recipe(recipe_id: int, recipe_resource: RecipeResource = Depends()) -> Any:
    return await recipe_resource.get(recipe_id)

@router.patch("/recipe/{recipe_id}", response_model=dict)
    async def update_recipe(recipe_id: int, recipe_resource: RecipeResource = Depends()) -> Any:
    return await recipe_resource.patch(recipe_id)

@router.delete("/recipe/{recipe_id}", response_model=dict)
async def delete_recipe(recipe_id: int, recipe_resource: RecipeResource = Depends())-> Any:
    return await recipe_resource.delete(recipe_id)

# Trasy dla planu posiłków
@router.get("/meal_plan", response_model=list)
    async def choose_meal(choose_meal_resource: ChooseMealResource = Depends()) -> Any:
    return await choose_meal_resource.get()

@router.post("/meal_plan", response_model=dict)
    async def create_meal_plan(choose_meal_resource: ChooseMealResource = Depends()) -> Any:
    return await choose_meal_resource.post()

# Trasy dla harmonogramu
@router.get("/schedule", response_model=dict)
async def get_schedule(schedule_resource: ScheduleResource = Depends()) -> Any:
    return await schedule_resource.get()

# Trasa dla listy zakupów
@router.get("/shopping_list", response_model=dict)
async def get_shopping_list(shopping_list_resource: ShoppingListResource = Depends()) -> Any:
    return await shopping_list_resource.get()
