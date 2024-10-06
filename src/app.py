from flask import Flask
from flask_restful import Api
from src.config import create_app
from src.routes import register_routes

def create_flask_app() -> Flask:
    app: Flask = create_app()
    api = Api(app)
    register_routes(app, api)
    return app

app: Flask = create_flask_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
