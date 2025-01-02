import pika
import json
from flask import current_app
from app.models import Book, Borrowing, db
from datetime import datetime, timedelta

def on_borrow_book_message(ch, method, properties, body):
    with current_app.app_context():
        # Parse the message
        message = json.loads(body)
        user_id = message.get('user_id')
        book_id = message.get('book_id')

        current_app.logger.info(f"Received borrow request from user {user_id} and book {book_id}")

        # Proceed with the borrow book logic
        book = Book.query.get(book_id)
        if not book:
            current_app.logger.error(f"Book with ID {book_id} not found.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if book.available_copies <= 0:
            current_app.logger.warning(f"No copies available for book {book_id}.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        return_by = datetime.utcnow() + timedelta(days=14)  # Set return date
        borrowing = Borrowing(book_id=book.id, user_id=user_id, return_by=return_by)

        book.available_copies -= 1
        db.session.add(borrowing)
        db.session.commit()

        # Acknowledge the message was processed
        current_app.logger.info(f"Book borrowed successfully for user {user_id}, book {book_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming():
    # Set up RabbitMQ connection and consumer
    try:
        # Get the Flask app object
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))  # Change 'rabbitmq' to your host if needed
        channel = connection.channel()

        # Declare the queue to consume from
        channel.queue_declare(queue='borrow_queue', durable=True)

        # Set up the consumer callback
        channel.basic_consume(queue='borrow_queue', on_message_callback=on_borrow_book_message)

        current_app.logger.info("Starting to consume messages...")
        # Start consuming
        channel.start_consuming()

    except Exception as e:
        current_app.logger.error(f"Error in consuming messages: {str(e)}")
