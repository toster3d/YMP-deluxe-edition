from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error='Username can only contain letters, numbers, and underscores'
            )
        ]
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=50),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                error='Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character'
            )
        ]
    )

class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error='Username can only contain letters, numbers, and underscores'
            )
        ]
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required for registration",
            "invalid": "Invalid email address"
        }
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=50),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                error='Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character'
            )
        ]
    )
    confirmation = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=50),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                error='Password confirmation must meet the password requirements'
            )
        ]
    )

class RecipeSchema(Schema):
    meal_name = fields.Str(required=True)
    meal_type = fields.Str(required=True)
    ingredients = fields.Str(required=False)
    instructions = fields.Str(required=False)

class PlanSchema(Schema):
    selected_date = fields.Date(required=True, format="%A %d %B %Y")
    user_plan = fields.String(required=True)
    meal_name = fields.String(required=True)

class RecipeUpdateSchema(Schema):
    meal_name = fields.Str(required=False)
    meal_type = fields.Str(required=False)
    ingredients = fields.Str(required=False)
    instructions = fields.Str(required=False)
