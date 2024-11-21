from datetime import timedelta
from typing import Any, cast

from flask import current_app, jsonify, make_response, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt, jwt_required  # type: ignore
from flask_restful import Resource
from pydantic import ValidationError

from extensions import db as db_extension
from services.user_auth import (
    InvalidCredentialsError,
    MissingCredentialsError,
    RegistrationError,
    UserAuth,
)
from token_storage import RedisTokenStorage

from .pydantic_schemas import LoginSchema, RegisterSchema


class AuthResource(Resource):
    def post(self) -> Response:
        data: dict[str, str] | None = request.get_json()
        if data is None:
            current_app.logger.warning("No input data provided for login.")
            return make_response(jsonify({"message": "No input data provided"}), 400)
        
        try:
            login_data = LoginSchema(**data)
        except ValidationError as err:
            current_app.logger.warning(f"Validation error: {err.errors()}")
            return make_response(jsonify({"message": "Invalid input data."}), 400)

        user_auth: UserAuth = UserAuth(db_extension)
        try:
            access_token: str = user_auth.login(login_data.username, login_data.password)
            return make_response(jsonify({
                "message": "Login successful!", 
                "access_token": access_token
            }), 200)
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

        try:
            register_data = RegisterSchema(**data)
        except ValidationError as err:
            current_app.logger.warning(f"Validation error: {err.errors()}")
            return make_response(jsonify({"message": "Invalid input data."}), 400)

        user_auth: UserAuth = UserAuth(db_extension)
        try:
            user_auth.register(
                register_data.username, 
                register_data.email, 
                register_data.password, 
                register_data.confirmation
            )
            return make_response(jsonify({"message": "Registration successful!"}), 201)
        except RegistrationError as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return make_response(jsonify({"error": "Registration failed."}), 500)


class LogoutResource(Resource):
    @jwt_required()
    def post(self) -> Response:
        try:
            jwt_data: dict[str, Any] = get_jwt()
            jti: str = jwt_data['jti']
            token_storage = cast(RedisTokenStorage, current_app.config['token_storage'])
            token_storage.store(
                jti, 
                expires_delta=cast(timedelta, current_app.config['JWT_ACCESS_TOKEN_EXPIRES']) 
            )
            return make_response(jsonify({"message": "Logout successful!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return make_response(jsonify({"message": "An error occurred during logout."}), 500)