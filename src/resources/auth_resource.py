from flask import jsonify, request, make_response, current_app
from flask.wrappers import Response
from flask_restful import Resource # type: ignore
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError
from typing import Any
from src.services.user_auth import UserAuth
from .schemas import LoginSchema, RegisterSchema

class AuthResource(Resource): # type: ignore    
    def post(self) -> Response:
        data = request.get_json()
        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema = LoginSchema()
        try:
            validated_data: dict[str, str] = schema.load(data)
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 400)

        username: str = validated_data['username']
        password: str = validated_data['password']

        user_auth = UserAuth(current_app.config['db'])
        success, result = user_auth.login(username, password)

        if not success:
            return make_response(jsonify({"message": result}), 400)

        return make_response(jsonify({"message": "Login successful!", "access_token": result}), 200)


class RegisterResource(Resource): # type: ignore
    def post(self) -> Response:
        data = request.get_json()
        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema = RegisterSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 400)

        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        confirmation = validated_data['confirmation']

        user_auth = UserAuth(current_app.extensions['sqlalchemy'].db) 
        success, result = user_auth.register(username, email, password, confirmation)

        if not success:
            return make_response(jsonify({"message": result}), 400)

        return make_response(jsonify({"message": "Registration successful!"}), 201)


class LogoutResource(Resource): # type: ignore  
    @jwt_required()
    def post(self) -> Response:
        try:
            jti = get_jwt()['jti'] 
            current_app.config['JWT_BLACKLIST'].add(jti)
            return make_response(jsonify({"message": "Logout successful!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return make_response(jsonify({"message": "An error occurred during logout."}), 500)
