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
the **User Service** consumes to notify the user about the unavailability in real time through an e-mail (using `Flask-Mail`).

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

---

## A detailed view of the microservices

### 1. **Authentification Microservice**
The Authentification Microservice handles user authentication and registration.
It provides REST API endpoints for user management and generates secure JWT tokens for authentication.

**Key Features**
- User registration with input validation.
- Login functionality with secure password hashing and verification.
- JWT token generation for authenticated access.

**Main Components**
- **User Model**: Represents user data including `username`, `password_hash`, `name`, and `role` (user or librarian).
- **REST API Endpoints**:
  - `/register`: Register a new user.
  - `/login`: Authenticate a user and return a JWT token.

This is the corresponding UML diagram generated with Python's `graphviz` library:

![authUML](https://github.com/DiaconuAna/SOA-App/blob/main/Resources/AuthUML.png)

## 2. **Book Microservice**
The Book Microservice manages the library's books, borrowings, and waiting lists. It provides functionality for adding, searching, and managing books, and supports integration with RabbitMQ for borrowing events.

### **Key Features**
- Add new books with details like title, author, ISBN, and available copies.
- Search books by title or author.
- Manage borrowings and waiting lists.

### **Main Components**
- **Book Model**: Stores book details such as `title`, `author`, `isbn`, and `available_copies`.
- **Borrowing Model**: Tracks user borrowings, including `borrowed_on` and `return_by` dates.
- **WaitingList Model**: Maintains a list of users waiting for unavailable books.
- **REST API Endpoints**:
  - `/add`: Add a new book (librarian only).
  - `/all_books`: Retrieve all books.
  - `/borrowed_books`: Get books borrowed by a user.
  - `/search`: Search books by title.
  - `/search_by_author`: Search books by author.

This is the corresponding UML diagram generated with Python's `graphviz` library:

![bookUML](https://github.com/DiaconuAna/SOA-App/blob/main/Resources/BookUML.png)

## 3. **User Microservice**
The User Microservice manages user profiles, borrowing actions, and communication with the Book Microservice via RabbitMQ. It ensures secure access using JWT tokens.

### **Key Features**
- Retrieve and update user profiles.
- Handle borrowing and returning of books with RabbitMQ integration.
- Fetch all users (for librarians).

### **Main Components**
- **User Model**: Represents user profiles including `username`, `name`, `role`, and `created_at`.
- **REST API Endpoints**:
  - `/profile`: Retrieve or create a user profile.
  - `/borrow`: Send a borrow request via RabbitMQ.
  - `/return`: Send a return request via RabbitMQ.
  - `/users`: Fetch all users (for librarians).
- **Messaging Integration**:
  - `send_borrow_request`: Sends borrow requests to RabbitMQ.
  - `send_return_request`: Sends return requests to RabbitMQ.

This is the corresponding UML diagram generated with Python's `graphviz` library:

![userUML](https://github.com/DiaconuAna/SOA-App/blob/main/Resources/UserUML.png)
