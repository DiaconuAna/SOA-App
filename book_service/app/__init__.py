from flask import Flask

from app.extensions import db, jwt
from app.routes import book_bp
from config import Config

import logging

from flask_migrate import Migrate

migrate = Migrate()
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.logger.info("Hello, BOOK SERVICE HERE")
    app.logger.debug(f"JWT_SECRET_KEY: {app.config['JWT_SECRET_KEY']}")

    db.init_app(app)
    jwt.init_app(app)
    # setup database migrations
    migrate.init_app(app, db)

    app.register_blueprint(book_bp, url_prefix='/book')

    return app