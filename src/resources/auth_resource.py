from typing import Any, Literal
from flask.wrappers import Response
from flask_restful import Resource
from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt # type: ignore
from marshmallow import ValidationError, Schema, fields, validate


class AuthSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error='Username can only contain letters, numbers, and underscores'
            )
        ],
        error_messages={
            "required": "Username is required",
            "invalid": "Invalid username"
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
        ],
        error_messages={
            "required": "Password is required",
            "invalid": "Password does not meet security requirements"
        }
    )

class UserRegistrationSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error='Username can only contain letters, numbers, and underscores'
            )
        ],
        error_messages={
            "required": "Username is required",
            "invalid": "Invalid username"
        }
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required",
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
        ],
        error_messages={
            "required": "Password is required",
            "invalid": "Password does not meet security requirements"
        }
    )
    confirmation = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=50),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                error='Password confirmation must contain at least one lowercase letter, one uppercase letter, one digit, and one special character'
            )
        ],
        error_messages={
            "required": "Password confirmation is required",
            "invalid": "Password confirmation does not meet security requirements"
        }
    )

class AuthResource(Resource):
    def get(self) -> tuple[dict[str, str], int]:
        return {"message": "Please use POST to authenticate"}, 200
    
    def post(self) -> Response:
        user_auth: Any = current_app.config['services']['user_auth']
        data: Any = request.get_json()
        schema = AuthSchema()
        try:
            validated_data: Any = schema.load(data)
        except ValidationError as err:
            response: Response = jsonify({"errors": err.messages}) # type: ignore
            response.status_code = 400
            return response
        
        username = validated_data['username']
        password = validated_data['password']
        
        authentication_result, message = user_auth.authenticate(username, password)
        if authentication_result:
            access_token = create_access_token(identity=username)
            response = jsonify({"message": "Authentication successful!", "access_token": access_token})
            response.status_code = 200
            return response
        response = jsonify({"message": message})
        response.status_code = 400
        return response

class RegisterResource(Resource):
    def get(self) -> tuple[dict[str, str], int]:
        return {"message": "Please use POST to register"}, 200
    
    def post(self) -> Response:
        user_auth: Any = current_app.config['services']['user_auth']
        data: Any = request.get_json()
        
        schema = UserRegistrationSchema()
        try:
            validated_data: Any = schema.load(data)
        except ValidationError as err:
            response: Response = jsonify({"errors": err.messages}) # type: ignore
            response.status_code = 400
            return response
        
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        confirmation = validated_data['confirmation']
        
        if password != confirmation:
            response = jsonify({"message": "Hasła nie pasują do siebie"})
            response.status_code = 400
            return response
        
        success, message = user_auth.register(username, email, password, confirmation)
        if success:
            access_token: str = create_access_token(identity=username)
            response = jsonify({"message": "Registration successful!", "access_token": access_token})
            response.status_code = 200
            return response
        response = jsonify({"message": message})
        response.status_code = 400
        return response

class LogoutResource(Resource):
    @jwt_required()
    def post(self) -> tuple[Response, Literal[401]] | Response:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({"message": "User is not logged in"}), 401
        jti: str = get_jwt()["jti"] # type: ignore
        user_auth: Any = current_app.config['services']['user_auth']
        if not hasattr(user_auth, 'add_token_to_blocklist'):
            raise AttributeError("Method 'add_token_to_blocklist' does not exist in user_auth service")
        user_auth.add_token_to_blocklist(jti)
        response = jsonify({"message": "Logout successful!"})
        response.status_code = 200
        return response


