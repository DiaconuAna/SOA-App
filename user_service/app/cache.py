import queue

# Shared queue for storing responses from RabbitMQ consumer
borrow_response_cache = queue.Queue()
return_response_cache = queue.Queue()