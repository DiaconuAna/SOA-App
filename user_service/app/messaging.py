import pika
import json
from flask import current_app
from app.cache import borrow_response_cache


def start_borrow_response_consumer():
    with current_app.app_context():
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()

            # Declare the response queue
            channel.queue_declare(queue='borrow_response_queue', durable=True)

            # Define the callback function
            def on_borrow_response(ch, method, properties, body):
                response = json.loads(body)
                user_id = response['user_id']
                book_id = response['book_id']
                status = response['status']
                message = response['message']

                # Log or process the response
                current_app.logger.info(f"Borrow response received for user {user_id}: {status} - {message}")
                # Put the response in the shared queue
                borrow_response_cache.put(response)
                # Acknowledge the message
                ch.basic_ack(delivery_tag=method.delivery_tag)


            # Start consuming
            channel.basic_consume(queue='borrow_response_queue', on_message_callback=on_borrow_response)
            current_app.logger.info("Listening for borrow responses...")
            channel.start_consuming()
        except Exception as e:
            current_app.logger.error(f"Error in borrow response consumer: {str(e)}")
            return {'status': 'failure', 'message': 'Error processing your borrow request.'}


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
        channel.queue_declare(queue='borrow_request_queue', durable=True)

        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key='borrow_request_queue',
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