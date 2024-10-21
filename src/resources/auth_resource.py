from flask import jsonify, request, make_response, current_app
from flask.wrappers import Response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt # type: ignore
from marshmallow import ValidationError
from services.user_auth import UserAuth, MissingCredentialsError, InvalidCredentialsError, RegistrationError
from .schemas import LoginSchema, RegisterSchema
from extensions import db as db_extension

class AuthResource(Resource): 
    def post(self) -> Response:
        data: dict[str, str] | None = request.get_json()
        if not data:
            current_app.logger.warning("No input data provided for login.")
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema: LoginSchema = LoginSchema()
        try:
            validated_data: dict[str, str] = schema.load(data)  # type: ignore
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 400)  # type: ignore

        username: str = validated_data['username']
        password: str = validated_data['password']

        user_auth: UserAuth = UserAuth(db_extension)
        try:
            access_token: str = user_auth.login(username, password)
            return make_response(jsonify({"message": "Login successful!", "access_token": access_token}), 200)
        except MissingCredentialsError as e:
            return make_response(jsonify({"error": str(e)}), 400)
        except InvalidCredentialsError as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)


class RegisterResource(Resource):
    def post(self) -> Response:
        data: dict[str, str] | None = request.get_json()
        if not data:
            return make_response(jsonify({"message": "No input data provided"}), 400)

        schema: RegisterSchema = RegisterSchema()
        try:
            validated_data: dict[str, str] = schema.load(data)  # type: ignore
        except ValidationError as err:
            return make_response(jsonify({"errors": err.messages}), 400)  # type: ignore

        username: str = validated_data['username']
        email: str = validated_data['email']
        password: str = validated_data['password']
        confirmation: str = validated_data['confirmation']

        user_auth: UserAuth = UserAuth(db_extension) 
        try:
            user_auth.register(username, email, password, confirmation)
            return make_response(jsonify({"message": "Registration successful!"}), 201)
        except RegistrationError as e:
            return make_response(jsonify({"error": str(e)}), 500)


class LogoutResource(Resource):
    @jwt_required()
    def post(self) -> Response:
        try:
            jti: str = get_jwt()['jti']  # type: ignore
            current_app.config['JWT_BLACKLIST'].add(jti)  # type: ignore
            return make_response(jsonify({"message": "Logout successful!"}), 200)
        except Exception as e:
            current_app.logger.error(f"Error during logout: {str(e)}")
            return make_response(jsonify({"message": "An error occurred during logout."}), 500)
