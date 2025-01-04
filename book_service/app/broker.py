import pika
import json
from flask import current_app
from app.models import Book, Borrowing, db, WaitingList
from datetime import datetime, timedelta
from kafka import KafkaProducer
import os

###########################
# KAFKA PRODUCER SETUP
###########################

producer = KafkaProducer(
    bootstrap_servers='kafka1:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_borrow_request(book_id, user_id):
    """Publishes a borrow request to the Kafka topic when a book is unavailable."""
    event = {
        "book_id": book_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.send('borrow-requests', event)
    current_app.logger.info(f"Published borrow request to Kafka: {event}")


def notify_user_book_available(user_id, book_id):
    """Notify the user that the book is available."""
    event = {
        "user_id": user_id,
        "book_id": book_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.send('book-availability', event)  # Publish a Kafka message to notify the user
    current_app.logger.info(f"Published book availability notification for User {user_id} and Book {book_id}")

###########################
# BORROW BOOK
###########################

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
                response['message'] = f"No copies available for book {book_id}. Subscribed."
                current_app.logger.warning(response['message'])

                # Add user to the waiting list
                waiting_list_entry = WaitingList(book_id=book.id, user_id=user_id)
                db.session.add(waiting_list_entry)
                db.session.commit()

                # Publish event to Kafka for borrow requests
                # publish_borrow_request(book_id, user_id)
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


def start_borrow_request_consumer():
    # Set up RabbitMQ connection and consumer
    try:
        # Get the Flask app object
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))  # Change 'rabbitmq' to your host if needed
        channel = connection.channel()

        # Declare the queue to consume from
        channel.queue_declare(queue='borrow_request_queue', durable=True)

        # Set up the consumer callback
        channel.basic_consume(queue='borrow_request_queue', on_message_callback=on_borrow_book_message)

        current_app.logger.info("Started listening for borrow requests...")
        # Start consuming
        channel.start_consuming()

    except Exception as e:
        current_app.logger.error(f"Error in consuming borrow messages: {str(e)}")

###########################
# RETURN BOOK
###########################

def send_return_response(user_id, book_id, status, message):
    """Send the return response back to User Service via RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the response queue (if not already declared)
        channel.queue_declare(queue='return_response_queue', durable=True)

        response_message = json.dumps({
            "user_id": user_id,
            "book_id": book_id,
            "status": status,
            "message": message
        })
        channel.basic_publish(
            exchange='',
            routing_key='return_response_queue',
            body=response_message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )
        connection.close()
    except Exception as e:
        print(f"Error sending response: {e}")


def on_return_request(ch, method, properties, body):
    """Callback function to handle return requests from User Service."""
    try:
        request_data = json.loads(body)
        user_id = request_data['user_id']
        book_id = request_data['book_id']

        # Find the borrowing record for the book and user
        borrowing = Borrowing.query.filter_by(user_id=user_id, book_id=book_id, returned_on=None).first()

        if not borrowing:
            # No active borrowing record found
            send_return_response(user_id, book_id, 'failure', 'Book not found or not borrowed')
        else:
            # Mark the book as returned
            borrowing.returned_on = datetime.utcnow()
            db.session.commit()

            # Increase available copies of the book
            book = Book.query.filter_by(id=book_id).first()
            if book:
                book.available_copies += 1
                db.session.commit()

                # Check if there are users in the waiting list
                waiting_list = WaitingList.query.filter_by(book_id=book_id).all()
                if waiting_list:
                    for entry in waiting_list:
                        # Notify users in the waiting list that the book is now available
                        notify_user_book_available(entry.user_id, book_id)

                    # Remove users from the waiting list after notifying
                    WaitingList.query.filter_by(book_id=book_id).delete()
                    db.session.commit()

            send_return_response(user_id, book_id, 'success', f'Book "{book.title}" returned successfully')

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        send_return_response(user_id, book_id, 'failure', f'Error processing return request: {str(e)}')
        print(f"Error processing return request: {e}")


def start_return_request_consumer():
    """Start consuming return requests from User Service."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the request queue
        channel.queue_declare(queue='return_request_queue', durable=True)

        # Start consuming the queue
        channel.basic_consume(queue='return_request_queue', on_message_callback=on_return_request)
        current_app.logger.info("Started listening for return requests...")
        channel.start_consuming()
    except Exception as e:
        current_app.logger.error(f"Error in return request consumer: {str(e)}")
