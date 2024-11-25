from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator


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
    def validate_password(cls, value: str) -> str:
        if (not any(c.islower() for c in value) or
            not any(c.isupper() for c in value) or
            not any(c.isdigit() for c in value) or
            not any(c in '@$!%*?&' for c in value)):
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
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get('password')
        if password and value != password:
            raise ValueError('Passwords do not match. Please ensure both passwords are identical.')
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
    selected_date: str = Field(
        ...,
        description="Date must be in format: Day DD Month YYYY"
    )
    recipe_id: int = Field(..., description="ID of the recipe to be used")
    meal_type: str = Field(..., description="Types of the meal are breakfast, lunch, dinner or dessert")

    @field_validator('selected_date')
    def validate_date_format(cls, value: str) -> str:
        # Możesz dodać walidację formatu daty, jeśli to konieczne
        return value