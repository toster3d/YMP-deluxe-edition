import sys
import os
from flask import Flask
from flask_restful import Api
from typing import Any, cast
from flask_jwt_extended import JWTManager # type: ignore
from config import create_app
from routes import register_routes
from extensions import db
import redis
from token_storage import RedisTokenStorage

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api: Api = Api(app)
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader # type: ignore
    def check_if_token_in_blocklist(jwt_header: Any, jwt_payload: Any) -> bool: #type: ignore
        jti: str = jwt_payload['jti']
        token_storage = cast(RedisTokenStorage, app.config['token_storage'])
        return token_storage.exists(jti)

    register_routes(app, api)
    
    with app.app_context():
        db.create_all()
        app.config['db'] = db
        
        redis_pool = redis.ConnectionPool(
            host=cast(str, app.config['REDIS_HOST']),
            port=cast(int, app.config['REDIS_PORT']),
            decode_responses=True
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        token_storage = RedisTokenStorage(redis_client)
        app.config['token_storage'] = token_storage
    
    return app

app = create_flask_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)