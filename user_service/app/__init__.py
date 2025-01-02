import threading

from flask import Flask

from app.extensions import db, jwt
from app.routes import user_bp
from config import Config

import logging

from flask_migrate import Migrate
from app.messaging import start_borrow_response_consumer  # Import the RabbitMQ logic

migrate = Migrate()
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    # setup database migrations
    migrate.init_app(app, db)

    app.register_blueprint(user_bp, url_prefix='/user')

    # Background thread for RabbitMQ consumer
    def start_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_borrow_response_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ user service consumer thread started.")

    # Start the consumer thread when the app starts
    start_consumer_thread()

    return app