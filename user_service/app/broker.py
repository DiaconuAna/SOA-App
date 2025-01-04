import pika
import json
from flask import current_app
from app.cache import borrow_response_cache, return_response_cache
from kafka import KafkaConsumer

#####################################
# KAFKA CONSUMER FOR BOOK BORROWING
#####################################

def start_kafka_notification_consumer():
    """Starts a Kafka consumer to listen for notifications about book availability."""
    with current_app.app_context():
        try:
            # Create a Kafka consumer

            # consumer = KafkaConsumer(
            #     'borrow-requests',
            #     bootstrap_servers='kafka1:9092',
            #     group_id='user-service-group',
            #     value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            #     auto_offset_reset='earliest'
            # )
            consumer = KafkaConsumer(
                'book-availability',
                bootstrap_servers='kafka1:9092',
                group_id='user-service-group',
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest'
                        )

            current_app.logger.info("Kafka consumer for book availability notifications started.")

            # Process incoming messages
            for message in consumer:
                event = message.value
                user_id = event.get('user_id')
                book_id = event.get('book_id')
                timestamp = event.get('timestamp')

                current_app.logger.info(
                    f"Received Kafka notification event: User {user_id} is waiting for Book {book_id} (at {timestamp})."
                )

                # Notify the user (Example: Send email or push notification)
                current_app.logger.info(
                    f"Notification sent to User {user_id} about Book {book_id} availability."
                )

        except Exception as e:
            current_app.logger.error(f"Error in Kafka notification consumer: {str(e)}")

###########################
# BORROW BOOK
###########################

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


###########################
# RETURN BOOK
###########################

def send_return_request(user_id, book_id):
    """Send a return request message to the Book Service via RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the return request queue
        channel.queue_declare(queue='return_request_queue', durable=True)

        request_message = json.dumps({
            "user_id": user_id,
            "book_id": book_id
        })

        # Send the request to the return_request_queue
        channel.basic_publish(
            exchange='',
            routing_key='return_request_queue',
            body=request_message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )

        current_app.logger.info(f"Sent return request for user {user_id} and book {book_id}")
        connection.close()

    except Exception as e:
        current_app.logger.error(f"Error sending return request: {e}")


def start_return_response_consumer():
    """Listen for the return response from Book Service."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()

        # Declare the response queue (if not already declared)
        channel.queue_declare(queue='return_response_queue', durable=True)

        def on_return_response(ch, method, properties, body):
            """Handle the return response message."""
            response = json.loads(body)
            user_id = response['user_id']
            book_id = response['book_id']
            status = response['status']
            message = response['message']

            # Log the response or use it to update the front-end
            current_app.logger.info(f"Return response received for user {user_id}: {status} - {message}")
            return_response_cache.put(response)
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Start consuming
        channel.basic_consume(queue='return_response_queue', on_message_callback=on_return_response)
        current_app.logger.info("Listening for return responses...")
        channel.start_consuming()
    except Exception as e:
        current_app.logger.error(f"Error in return response consumer: {str(e)}")
