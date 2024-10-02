from typing import Any, Literal
from flask.wrappers import Response
from flask_restful import Resource
from flask import current_app, session, jsonify, request
from ..helpers.login_required_decorator import login_required
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validate
from src.schemas.user_schema import UserRegistrationSchema

class AuthSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=1), error_messages={"required": "Username is required"})
    password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={"required": "Password is required"})

class AuthResource(Resource):
    def post(self) -> tuple[Response, int]:
        user_auth: Any = current_app.config['services']['user_auth']
        data = request.get_json()
        
        schema = AuthSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        username = validated_data['username']
        password = validated_data['password']
        
        success, message = user_auth.authenticate(username, password)
        if success:
            access_token = create_access_token(identity=username)
            return jsonify({"message": "Authentication successful!", "access_token": access_token}), 200
        return jsonify({"message": message}), 400

class RegisterResource(Resource):
    def get(self) -> tuple[Response, int]:
        return jsonify({"message": "Please use POST to register"}), 200
    
    def post(self) -> tuple[Response, int]:
        user_auth = current_app.config['services']['user_auth']
        data = request.get_json()
        
        schema = UserRegistrationSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        confirmation = validated_data['confirmation']
        
        if password != confirmation:
            return jsonify({"message": "Passwords do not match"}), 400
        
        success, message = user_auth.register(username, email, password, confirmation)
        if success:
            access_token = create_access_token(identity=username)
            return jsonify({"message": "Registration successful!", "access_token": access_token}), 200
        return jsonify({"message": message}), 400

@login_required
def logout() -> tuple[Response, Literal[200]]:
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200


