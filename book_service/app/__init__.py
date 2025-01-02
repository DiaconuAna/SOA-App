from flask import Flask

from app.extensions import db, jwt
from app.routes import book_bp
from app.consumer import start_consuming
from config import Config
import threading

import logging

from flask_migrate import Migrate

migrate = Migrate()
logging.basicConfig(level=logging.DEBUG)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # app.logger.info("Hello, BOOK SERVICE HERE")
    # app.logger.debug(f"JWT_SECRET_KEY: {app.config['JWT_SECRET_KEY']}")

    db.init_app(app)
    jwt.init_app(app)
    # setup database migrations
    migrate.init_app(app, db)

    app.register_blueprint(book_bp, url_prefix='/book')

    # Background thread for RabbitMQ consumer
    # Background thread for RabbitMQ consumer
    def start_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_consuming()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ consumer thread started.")

    # Start the consumer thread when the app starts
    start_consumer_thread()

    return app