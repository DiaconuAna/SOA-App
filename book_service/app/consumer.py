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

        response = {'user_id': user_id, 'book_id': book_id, 'status': 'failure', 'message': ''}

        try:
            book = Book.query.get(book_id)
            if not book:
                response['message'] = f"Book with ID {book_id} not found."
                current_app.logger.error(response['message'])
            elif book.available_copies <= 0:
                response['message'] = f"No copies available for book {book_id}."
                current_app.logger.warning(response['message'])
            else:
                # Check if the user has already borrowed this book
                existing_borrow = Borrowing.query.filter_by(
                    user_id=user_id,
                    book_id=book_id,
                    returned_on=None  # Assuming you have a `returned` field to indicate the return status
                ).first()

                if existing_borrow:
                    response['message'] = f"User {user_id} has already borrowed book {book_id}."
                    current_app.logger.warning(response['message'])
                else:
                    return_by = datetime.utcnow() + timedelta(days=14)  # Set return date
                    borrowing = Borrowing(book_id=book.id, user_id=user_id, return_by=return_by)

                    book.available_copies -= 1
                    db.session.add(borrowing)
                    db.session.commit()

                    response['status'] = 'success'
                    response['message'] = f"Book borrowed successfully for user {user_id}."
                    current_app.logger.info(response['message'])

        except Exception as e:
            response['message'] = f"Error processing borrow request: {str(e)}"
            current_app.logger.error(response['message'])

        # Send response back to User Service
        send_borrow_response(response)
        ch.basic_ack(delivery_tag=method.delivery_tag)


def send_borrow_response(response):
    try:
        # Set up RabbitMQ connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the response queue
        channel.queue_declare(queue='borrow_response_queue', durable=True)

        # Publish the response message
        channel.basic_publish(
            exchange='',
            routing_key='borrow_response_queue',
            body=json.dumps(response),
            properties=pika.BasicProperties(
                delivery_mode=2  # Persist the message
            )
        )

        current_app.logger.info(f"Sent borrow response: {response}")
        connection.close()
    except Exception as e:
        current_app.logger.error(f"Error sending borrow response: {str(e)}")


def start_consuming():
    # Set up RabbitMQ connection and consumer
    try:
        # Get the Flask app object
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))  # Change 'rabbitmq' to your host if needed
        channel = connection.channel()

        # Declare the queue to consume from
        channel.queue_declare(queue='borrow_request_queue', durable=True)

        # Set up the consumer callback
        channel.basic_consume(queue='borrow_request_queue', on_message_callback=on_borrow_book_message)

        current_app.logger.info("Starting to consume messages...")
        # Start consuming
        channel.start_consuming()

    except Exception as e:
        current_app.logger.error(f"Error in consuming messages: {str(e)}")
