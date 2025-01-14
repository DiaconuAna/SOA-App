import threading

from flask import Flask
from flask_cors import CORS

from app.extensions import db, jwt
from app.routes import user_bp
from config import Config

import logging

from flask_migrate import Migrate
from app.broker import start_borrow_response_consumer, start_return_response_consumer  # Import the RabbitMQ logic
from app.broker import start_kafka_notification_consumer

from flask_mail import Mail

migrate = Migrate()
logging.basicConfig(level=logging.DEBUG)

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    mail.init_app(app)

    db.init_app(app)
    jwt.init_app(app)
    # setup database migrations
    migrate.init_app(app, db)

    app.register_blueprint(user_bp, url_prefix='/user')

    # Background thread for RabbitMQ consumer
    def start_borrow_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_borrow_response_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ user service borrow consumer thread started.")

    def start_return_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_return_response_consumer()

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("RabbitMQ user service return consumer thread started.")

    def start_kafka_consumer_thread():
        def consume_in_thread():
            # Ensure the app context is available in the thread
            with app.app_context():
                start_kafka_notification_consumer(mail)

        consumer_thread = threading.Thread(target=consume_in_thread, daemon=True)
        consumer_thread.start()
        app.logger.info("Kafka borrow consumer thread started.")


    # Start the consumer threads when the app starts
    start_borrow_consumer_thread()
    start_return_consumer_thread()
    start_kafka_consumer_thread()

    return app