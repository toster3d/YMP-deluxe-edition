import sys
import os
from flask import Flask
from flask_restful import Api
from typing import Any, cast
from config import create_app
from routes import register_routes
from flask_jwt_extended import JWTManager
from extensions import db
from redis_client import RedisClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api: Api = Api(app)
    register_routes(app, api)
    
    with app.app_context():
        db.create_all()
        app.config['db'] = db
        redis_client = RedisClient()
        app.config['redis_client'] = redis_client
    
    return app

app = create_flask_app()
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader # type: ignore
def check_if_token_in_blocklist(jwt_header: Any, jwt_payload: Any) -> bool:
    jti: str = jwt_payload['jti']
    redis_client: RedisClient = cast(RedisClient, app.config['redis_client'])
    return redis_client.is_blacklisted(jti)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)