from flask_restful import Resource, reqparse
from flask import current_app, session, jsonify, render_template, make_response, request
from .. import db
from ..helpers.login_required_decorator import login_required

class AuthResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("username", type=str, required=True, help="Username is required")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")
    
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('login.html'), 200, headers)
    
    def post(self):
        user_auth = current_app.config['services']['user_auth']
        args = self.parser.parse_args()
        username = args['username']
        password = args['password']
        
        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400
        
        success = user_auth.login(username, password)
        
        if success:
            session['user_id'] = user_auth.get_user_id(username)
            return jsonify({"message": "Login successful!"})
        return jsonify({"message": "Invalid credentials"}), 401

class RegisterResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("username", type=str, required=True, help="Username is required")
        self.parser.add_argument("email", type=str, required=True, help="Email is required")
        self.parser.add_argument("password", type=str, required=True, help="Password is required")
        self.parser.add_argument("confirmation", type=str, required=True, help="Password confirmation is required")
    
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('register.html'), 200, headers)
    
    def post(self):
        user_auth = current_app.config['services']['user_auth']
        args = self.parser.parse_args()
        username = args['username']
        email = args['email']
        password = args['password']
        confirmation = args['confirmation']
        
        if not all([username, email, password, confirmation]):
            return jsonify({"message": "All fields are required"}), 400
        
        success, message = user_auth.register(username, email, password, confirmation)
        if success:
            return jsonify({"message": "Registration successful!"})
        return jsonify({"message": message}), 400

@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200


