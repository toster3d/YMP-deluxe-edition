from flask import Flask
from flask_restful import Api
from . import create_app, configure_app
from .routes import register_routes

app = create_app()
configure_app(app)
api = Api(app)

register_routes(app, api)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
