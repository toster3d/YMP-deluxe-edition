from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from services.user_auth_manager import PasswordValidator


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")

class RegisterSchema(BaseModel):
    email: EmailStr = Field(
        description="Email is required for registration",
    )
    username: str = Field(
        min_length=3,
        max_length=30,
        description="Username must be between 3 and 30 characters long"
    )
    password: str = Field(
        min_length=8,
        max_length=50,
        description="Password must be at least 8 characters long and meet complexity requirements"
    )
    confirmation: str = Field(
        min_length=8,
        max_length=50,
        description="Password confirmation must match password"
    )

    @field_validator('confirmation')
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get('password')
        if password and value != password:
            raise ValueError('Passwords do not match. Please ensure both passwords are identical.')
        return value

    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        validator = PasswordValidator()
        if not validator.validate(value):
            raise ValueError('Password does not meet complexity requirements.')
        return value

class RecipeSchema(BaseModel):
    meal_name: str = Field(..., description="Name of the meal")
    meal_type: str = Field(..., description="Type of the meal")
    ingredients: list[str] = Field(default_factory=list, description="List of ingredients required for the meal")
    instructions: list[str] = Field(default_factory=list, description="Step-by-step instructions to prepare the meal")

class RecipeUpdateSchema(BaseModel):
    meal_name: str | None = None
    meal_type: str | None = None
    ingredients: list[str] | None = None
    instructions: list[str] | None = None

class PlanSchema(BaseModel):
    selected_date: datetime = Field(
        ...,
        description="Date must be in format: Day DD Month YYYY"
    )
    recipe_id: int = Field(..., description="ID of the recipe to be used")
    meal_type: str = Field(..., description="Types of the meal are breakfast, lunch, dinner or dessert")

class DateRangeSchema(BaseModel):
    start_date: date = Field(..., description="Start date in format: Day Month Year")
    end_date: date = Field(..., description="End date in format: Day Month Year")