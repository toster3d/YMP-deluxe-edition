from flask import Flask
from flask_restful import Api
from src.config import create_app
from src.routes import register_routes
from flask_jwt_extended import JWTManager
from typing import Any

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api = Api(app)
    register_routes(app, api)
    jwt = JWTManager(app) #type: ignore

    return app

app: Flask = create_flask_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

@jwt.token_in_blocklist_loader  # type: ignore
def check_if_token_in_blocklist(  # type: ignore
    jwt_header: dict[str, Any],
    jwt_payload: dict[str, Any]
) -> bool:
    jti: str = jwt_payload['jti']
    return jti in app.config['JWT_BLACKLIST']
