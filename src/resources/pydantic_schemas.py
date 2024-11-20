from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
import re

class LoginSchema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Username can only contain letters, numbers, and underscores"
    )
    password: str = Field(
        min_length=8,
        max_length=50,
        description="Password must meet complexity requirements"
    )

    @field_validator('password')
    def validate_password(class_reference, value: str) -> str:
        pattern: str = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$'
        if not re.match(pattern, value):
            raise ValueError(
                'Password must contain at least one lowercase letter, '
                'one uppercase letter, one digit, and one special character'
            )
        return value

class RegisterSchema(LoginSchema):
    email: EmailStr = Field(
        description="Email is required for registration",
    )
    confirmation: str = Field(
        min_length=8,
        max_length=50,
        description="Password confirmation must match password"
    )

    @field_validator('confirmation')
    def passwords_match(class_reference, value: str, info: ValidationInfo) -> str:
        if 'password' in info.data and value != info.data['password']:
            raise ValueError('Passwords do not match. Please ensure both passwords are identical.')
        return value

class RecipeSchema(BaseModel):
    meal_name: str = Field(..., description="Name of the meal")
    meal_type: str = Field(..., description="Type of the meal")
    ingredients: list[str] = Field(None, description="List of ingredients required for the meal")
    instructions: list[str] = Field(None, description="Step-by-step instructions to prepare the meal")

class RecipeUpdateSchema(BaseModel):
    meal_name: str | None = None
    meal_type: str | None = None
    ingredients: list[str] | None = None
    instructions: list[str] | None = None

class PlanSchema(BaseModel):
    selected_date: str = Field(
        ...,
        pattern=r'^[A-Za-z]+ \d{2} [A-Za-z]+ \d{4}$',
        description="Date must be in format: Day DD Month YYYY"
    )
    user_plan: str = Field(..., description="User plan details")
    meal_name: str = Field(..., description="Name of the meal")