import os
import sys
from typing import Any, cast

import redis
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, request
from flask_jwt_extended import JWTManager  # type: ignore
from flask_restful import Api
from markupsafe import escape

from config import create_app
from extensions import db
from routes import register_routes, router  # Importuj router z routes.py
from token_storage import RedisTokenStorage

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api: Api = Api(app)
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader  # type: ignore
    def check_if_token_in_blocklist(jwt_header: Any, jwt_payload: Any) -> bool:  # type: ignore
        jti: str = jwt_payload['jti']
        token_storage = cast(RedisTokenStorage, app.config['token_storage'])
        return token_storage.exists(jti)

    # Dodaj trasę do aplikacji Flask
    @app.route("/")
    def flask_main() -> str:
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)} from Flask!"

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

# Create the Flask app
flask_app = create_flask_app()

# Create the FastAPI app
fastapi_app = FastAPI()

# Mount the Flask app under a specific path
fastapi_app.mount("/v1", WSGIMiddleware(flask_app))  # Zmiana na /v1

# FastAPI routes
@fastapi_app.get("/v2")
async def read_main() -> dict[str, str]:
    return {"message": "Hello World from FastAPI"}

# Rejestracja routera
fastapi_app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app:fastapi_app",  # Poprawiono ścieżkę do aplikacji FastAPI
        host="0.0.0.0",
        port=5000,
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )