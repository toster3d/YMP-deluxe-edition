import json
from typing import Any, cast
from flask_restful import Resource
from flask import jsonify, request, make_response, current_app
from flask.wrappers import Response
from flask_jwt_extended import jwt_required, get_jwt # type: ignore 
from marshmallow import ValidationError
from services.user_auth import UserAuth, MissingCredentialsError, InvalidCredentialsError, RegistrationError
from .schemas import LoginSchema, RegisterSchema
from extensions import db as db_extension


class AuthResource(Resource):
    def post(self) -> Response:
        data = request.get_json()
        if data is None:
            current_app.logger.warning("No input data provided for login.")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema: LoginSchema = LoginSchema()
        try:
            validated_data = cast(dict[str, Any], schema.load(data))
        except ValidationError as err:
            current_app.logger.warning(f"Validation error: {json.dumps(err.messages)}") # type: ignore
            return make_response(jsonify({"message": "Invalid input data."}), 400)

        username = validated_data['username']
        password = validated_data['password']

        user_auth: UserAuth = UserAuth(db_extension)
        try:
            access_token: str = user_auth.login(username, password)
            return make_response(jsonify({"message": "Login successful!", "access_token": access_token}), 200)
        except MissingCredentialsError as e:
            current_app.logger.warning(f"Missing credentials: {e}")
            return make_response(jsonify({"error": "Missing credentials."}), 400)
        except InvalidCredentialsError as e:
            current_app.logger.warning(f"Invalid credentials: {e}")
            return make_response(jsonify({"error": "Invalid credentials."}), 401)
        except Exception as e:
            current_app.logger.error(f"Unexpected error during login: {e}")
            return make_response(jsonify({"error": "An unexpected error occurred."}), 500)


class RegisterResource(Resource):
    def post(self) -> Response:
        data: dict[str, str] | None = request.get_json()
        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema: RegisterSchema = RegisterSchema()
        try:
            validated_data = cast(dict[str, Any], schema.load(data))
        except ValidationError as err:
            current_app.logger.warning(f"Validation error: {err.messages}")  # type: ignore
            return make_response(jsonify({"message": "Invalid input data."}), 400)

        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        confirmation = validated_data['confirmation']

        user_auth: UserAuth = UserAuth(db_extension)
        try:
            user_auth.register(username, email, password, confirmation)
            return make_response(jsonify({"message": "Registration successful!"}), 201)
        except RegistrationError as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return make_response(jsonify({"error": "Registration failed."}), 500)


class LogoutResource(Resource): # type: ignore
    @jwt_required()
    def post(self) -> Response:
        try:
            jti = get_jwt()['jti'] # type: ignore
            current_app.config['JWT_BLACKLIST'].add(jti) # type: ignore
            return make_response(jsonify({"message": "Logout successful!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return make_response(jsonify({"message": "An error occurred during logout."}), 500)
