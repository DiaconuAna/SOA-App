# SOA-App
Library Management Application for Service Oriented Architecture class

## Introduction

This project is a microservice-based system designed to handle various functionalities related to
authentication, user and book management. The application is fully containerized using Docker, with
all its components orchestrated and managed through Docker Compose.

The system integrates several backend services developed in Python using Flask,
a microfrontend architecture built with Angular and Module Federation,
and an NGINX load-balanced API gateway for efficient routing. The application also contains
support for serverless functions using AWS Lambda. Message-based communication between micro-services is managed through RabbitMQ,
and event-streaming using Apache Kafka. The REST API is secured using JWT tokens to ensure safe authentication and authorization.

Here is an overview of each main component of the application:

### Backend Services

- **Auth Service**: Manages user authentication and token generation.
- **User Service**: Handles user-related data and operations such as fetching the profile of a user.
- **Book Service**: Provides book management functionalities with redundancy through a backup instance.

### API Gateway

The API Gateway is built with **NGINX**, and acts as a reverse proxy and load balancer (for the book microservice),
routing requests to the appropriate backend services and the AWS Lambda-based serverless function.

### Database Layer

Each microservice has a dedicated **PostgreSQL** instance for data isolation and integrity.

### Message brokers and event streaming

Message brokering is developed using **RabbitMQ**. This facilitates asynchronous communication between the **User Service**
and the **Book Service** to handle borrowing and returning books. When a user wants to borrow or return a book,
 the **User Service** sends a message to the **Book Service** via RabbitMQ to update the book's availability.

Event streaming is built using Apache Kafka to manage data streaming and real-time processing. In this context, Kafka is
used for event-driven communication between the **Book Service** and the **User Service**. When a user attempts to borrow
a book that is no longer available, the **Book Service** emits an event about the book's availability via Kafka, which
the **User Service** consumes to notify the user about the unavailability in real time

### FaaS

A **Lambda function** (`get-user-borrowings`) is used to demonstrate serverless computing. This function is built using
**AWS Lambda**, and is responsible for retrieving a list of books borrowed by a specific user. This allows the system
to handle user-specific data queries without needing a full-fledged backend service.
The function is deployed and managed using the **Serverless Framework**, for efficient deployment to AWS.

All of the above are illustrated in the following architecture diagram:

![backend_arch](https://github.com/DiaconuAna/SOA-App/blob/main/Resources/BackendArchitecture.png)

### Microfrontend Architecture

The front-end of the library management application is built as a microfrontend architecture using Module Federation
with Webpack. It consists of a **host** (`shell`) and three **microfrontends** (`auth`, `book`, and `user`) to provide
a modular and scalable interface.

This is illustrated in the following architecture diagram:

![frontend_arch](https://github.com/DiaconuAna/SOA-App/blob/main/Resources/FrontendArchitecture.png)
