from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from services.password_validator import PasswordValidator

MealType = Literal["breakfast", "lunch", "dinner", "dessert"]
VALID_MEAL_TYPES = ("breakfast", "lunch", "dinner", "dessert")


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str = Field(
        ..., 
        min_length=1,
        description="JWT access token"
    )
    token_type: str = Field("bearer", description="Token type")


class RegisterSchema(BaseModel):
    email: EmailStr = Field(
        description="Email is required for registration",
    )
    username: str = Field(
        min_length=3,
        max_length=30,
        description="Username must be between 3 and 30 characters long",
    )
    password: str = Field(
        min_length=8,
        max_length=50,
        description="Password must be at least 8 characters long and meet complexity requirements",
    )
    confirmation: str = Field(
        min_length=8,
        max_length=50,
        description="Password confirmation must match password",
    )

    @field_validator("confirmation")
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get("password")
        if password and value != password:
            raise ValueError(
                "Passwords do not match. Please ensure both passwords are identical."
            )
        return value

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        validator = PasswordValidator()
        if not validator.validate(value):
            raise ValueError("Password does not meet complexity requirements.")
        return value


class RecipeSchema(BaseModel):
    """Schema for recipe data validation."""
    
    model_config = ConfigDict(strict=True)

    meal_name: str = Field(
        ..., 
        description="Name of the meal",
        min_length=1,
        max_length=200,
    )
    meal_type: MealType = Field(
        ..., 
        description="Type of meal",
        examples=["breakfast", "lunch", "dinner", "dessert"],
    )
    ingredients: list[str] = Field(
        default_factory=list,
        description="List of ingredients required for the meal",
        examples=[["flour", "sugar", "eggs"]],
    )
    instructions: list[str] = Field(
        default_factory=list,
        description="Step-by-step instructions to prepare the meal",
        examples=[["Mix ingredients", "Bake for 30 minutes"]], 
    )

    @field_validator("ingredients", "instructions")
    @classmethod
    def validate_list_items(cls, v: list[str]) -> list[str]:
        """Validate that list items are non-empty strings."""
        if any(not item.strip() for item in v):
            raise ValueError("Input should be a valid string")
        return v

class RecipeUpdateSchema(BaseModel):
    meal_name: str | None = None
    meal_type: MealType | None = None
    ingredients: list[str] | None = None
    instructions: list[str] | None = None

    @field_validator("ingredients", "instructions")
    @classmethod
    def validate_list_items(cls, v: list[str] | None) -> list[str] | None:
        """Validate that list items are non-empty strings."""
        if v is not None:
            if any(not item.strip() for item in v):
                raise ValueError("Input should be a valid string")
        return v


class UserPlanSchema(BaseModel):
    user_id: int
    date: date
    breakfast: str | None = Field(None, description="Breakfast meal name")
    lunch: str | None = Field(None, description="Lunch meal name")
    dinner: str | None = Field(None, description="Dinner meal name")
    dessert: str | None = Field(None, description="Dessert meal name")

    model_config = ConfigDict(from_attributes=True)


class PlanSchema(BaseModel):
    selected_date: date = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    recipe_id: int = Field(..., gt=0, description="ID of the recipe")
    meal_type: MealType = Field(
        ..., description="Type of meal (breakfast, lunch, dinner, dessert)"
    )


class DateRangeSchema(BaseModel):
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")


class ScheduleResponse(BaseModel):
    date: date
    breakfast: str | None = None
    lunch: str | None = None
    dinner: str | None = None
    dessert: str | None = None


class ShoppingListResponse(BaseModel):
    """Schema for shopping list response."""
    ingredients: list[str] = Field(
        description="List of ingredients needed for planned meals"
    )
    current_date: str = Field(
        description="Current date in ISO format (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )


class ShoppingListRangeResponse(BaseModel):
    """Schema for shopping list date range response."""
    ingredients: list[str] = Field(
        description="List of ingredients needed for planned meals"
    )
    date_range: str = Field(
        description="Date range in format 'YYYY-MM-DD to YYYY-MM-DD'",
        pattern=r"^\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}$"
    )
