from flask import jsonify, request, make_response, current_app
from flask.wrappers import Response
from flask_restful import Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError
from typing import Any
from src.services.user_auth import UserAuth
from .schemas import LoginSchema, RegisterSchema
from src.models.recipes import User


class AuthResource(Resource):
    def post(self) -> Response:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400 # type: ignore

        schema = LoginSchema()
        try:
            validated_data: Any = schema.load(data)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400  # type: ignore

        username: str = validated_data['username']
        password: str = validated_data['password']

        user_auth = UserAuth(current_app.config['db'])
        success, result = user_auth.login(username, password)

        if not success:
            return jsonify({"message": result}), 400 # type: ignore

        return jsonify({"message": "Login successful!", "access_token": result}), 200 # type: ignore


class RegisterResource(Resource):
    def post(self) -> Response:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400 # type: ignore

        schema = RegisterSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400 # type: ignore

        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        confirmation = validated_data['confirmation']

        user_auth = UserAuth(current_app.extensions['sqlalchemy'].db) 
        success, result = user_auth.register(username, email, password, confirmation)

        if not success:
            return jsonify({"message": result}), 400 # type: ignore

        return jsonify({"message": "Registration successful!"}), 201 # type: ignore


class LogoutResource(Resource):
    @jwt_required()
    def post(self) -> Response:
        try:
            jti = get_jwt()['jti'] 
            current_app.config['JWT_BLACKLIST'].add(jti)
            return jsonify({"message": "Logout successful!"}), 200 # type: ignore
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return jsonify({"message": "An error occurred during logout."}), 500 # type: ignore
