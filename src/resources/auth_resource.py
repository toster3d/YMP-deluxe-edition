from flask import jsonify, request, current_app
from flask.wrappers import Response
from flask_jwt_extended import jwt_required, get_jwt  # type: ignore
from flask_restful import Resource
from marshmallow import ValidationError
from typing import Union, Any
from src.services.user_auth import UserAuth
from .schemas import LoginSchema, RegisterSchema


class AuthResource(Resource):
    def post(self) -> Union[tuple[dict[str, Any], int], tuple[Response, int]]:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        schema = LoginSchema()
        try:
            validated_data: Any = schema.load(data)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400  # type: ignore

        username: str = validated_data['username']
        password: str = validated_data['password']

        user_auth = UserAuth(current_app.config['db'])  # type: ignore
        success, result = user_auth.login(username, password)

        if not success:
            return jsonify({"message": result}), 400

        return jsonify({"message": "Login successful!", "access_token": result}), 200


class RegisterResource(Resource):
    def post(self) -> Union[tuple[dict[str, Any], int], tuple[Response, int]]:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        schema = RegisterSchema()
        try:
            validated_data: RegisterData = schema.load(data)  # type: ignore
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400  # type: ignore

        username: Any = validated_data['username']
        email: Any = validated_data['email']
        password: Any = validated_data['password']
        confirmation: Any = validated_data['confirmation']

        user_auth = UserAuth(current_app.config['db'])  # type: ignore
        success, result = user_auth.register(username, email, password, confirmation)

        if not success:
            return jsonify({"message": result}), 400

        return jsonify({"message": "Registration successful!"}), 200


class LogoutResource(Resource):
    @jwt_required()
    def post(self) -> Union[tuple[dict[str, str], int], tuple[Response, int]]:
        try:
            jti = get_jwt()['jti'] # type: ignore
            current_app.config['JWT_BLACKLIST'].add(jti) #type: ignore
            return jsonify({"message": "Logout successful!"}), 200
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return jsonify({"message": "An error occurred during logout."}), 500
