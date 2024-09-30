from flask_restful import Resource, reqparse
from flask import current_app, session, jsonify, render_template, make_response, request
from .. import db  # Ten import powinien teraz działać

def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        user_auth = current_app.config['services']['user_auth']
        username = request.form.get('username')
        password = request.form.get('password')
        success = user_auth.login(username, password)
        
        if success:
            session['user_id'] = user_auth.get_user_id(username)
            return jsonify({"message": "Logowanie udane!"})
        return jsonify({"message": "Nieprawidłowe dane uwierzytelniające"}), 401

def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        user_auth = current_app.config['services']['user_auth']
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        
        success, message = user_auth.register(username, email, password, confirmation)
        if success:
            return jsonify({"message": "Registration successful!"})
        return jsonify({"message": message}), 400

class AuthResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("username", type=str, required=True, help="Nazwa użytkownika jest wymagana")
        self.parser.add_argument("password", type=str, required=True, help="Hasło jest wymagane")
    
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('login.html'), 200, headers)
    
    def post(self):
        user_auth = current_app.config['services']['user_auth']
        args = self.parser.parse_args()
        username = args['username']
        password = args['password']
        success = user_auth.login(username, password)
        
        if success:
            session['user_id'] = user_auth.get_user_id(username)
            return jsonify({"message": "Logowanie udane!"})
        return jsonify({"message": "Nieprawidłowe dane uwierzytelniające"}), 401

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
        
        success, message = user_auth.register(username, email, password, confirmation)
        if success:
            return jsonify({"message": "Registration successful!"})
        return jsonify({"message": message}), 400


