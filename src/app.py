from flask_restful import Api
from flask import Flask 
from .config import create_app, configure_app
from .routes import register_routes # type: ignore

app: Flask = create_app()
app = configure_app(app)
api = Api(app)

register_routes(app, api)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
