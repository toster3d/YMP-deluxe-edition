from flask import Flask
from flask_restful import Api
from typing import Any
from src.config import create_app
from src.routes import register_routes
from flask_jwt_extended import JWTManager
from src.extensions import db

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api: Api = Api(app)
    register_routes(app, api)

    with app.app_context():
        db.create_all()
        app.config['db'] = db

    return app

app: Flask = create_flask_app()
jwt: JWTManager = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(
    jwt_header: Any,
    jwt_payload: Any
) -> bool:
    jti: str = jwt_payload['jti']
    return jti in app.config['JWT_BLACKLIST']

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
