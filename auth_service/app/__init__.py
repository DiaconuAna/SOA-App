from flask import Flask

from app.extensions import db, jwt
from app.routes import auth_bp
from config import Config
from flask_cors import CORS

from flask_migrate import Migrate

import logging

logging.basicConfig(level=logging.DEBUG)
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    jwt.init_app(app)
    # setup database migrations
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app