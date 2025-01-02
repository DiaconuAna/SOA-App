import pika
import json
from flask import current_app


def send_borrow_request(user_id, book_id):
    message = {
        'user_id': user_id,
        'book_id': book_id,
    }

    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the queue (ensure the queue exists before publishing)
        channel.queue_declare(queue='borrow_queue', durable=True)

        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key='borrow_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Persist the message
            )
        )

        current_app.logger.info(f"Sent borrow request for user {user_id} and book {book_id}")

        connection.close()

    except Exception as e:
        current_app.logger.error(f"Error sending borrow request: {str(e)}")
        raise e