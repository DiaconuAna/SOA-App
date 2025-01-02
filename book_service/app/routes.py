from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from app.models import Book, db, Borrowing
from app.utils import role_required
import os

book_bp = Blueprint('book', __name__)
HOST_NAME = os.environ.get('HOST_NAME')

@book_bp.route('/add', methods=['POST'])
@role_required('librarian')
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    available_copies = data.get('available_copies', 1)

    if not title or not author or not isbn:
        return jsonify({"msg": "Title, author and ISBN are required", "hostname": HOST_NAME}), 400

    # Ensure the ISBN is unique (optional validation)
    existing_book = Book.query.filter_by(isbn=isbn).first()
    if existing_book:
        return jsonify({"msg": "Book with this ISBN already exists", "hostname": HOST_NAME}), 400

    new_book = Book(title=title, author=author, isbn=isbn, available_copies=available_copies)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"msg": "Book added successfully", "hostname": HOST_NAME}), 201

@book_bp.route('/all_books', methods=['GET'])
@role_required('librarian', 'user')
def get_all_books():
    try:
        books = Book.query.all()

        if not books:
            return jsonify({"msg": "No books found", "hostname": HOST_NAME}), 404

        book_list = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "available_copies": book.available_copies
            } for book in books]

        return jsonify({"books": book_list, "hostname": HOST_NAME}), 200

    except Exception as e:
        return jsonify({"msg": f"Error retrieving books: {str(e)}", "hostname": HOST_NAME}), 500

@book_bp.route('/borrow', methods=['POST'])
@role_required('user')
def borrow_book():
    data = request.get_json()
    user_id = int(data.get('user_id'))
    book_id = data.get('book_id')

    if not user_id or not book_id:
        return jsonify({"msg": "User ID and Book ID are required", "hostname": HOST_NAME}), 400

    # Retrieve the book to be borrowed
    book = Book.query.get(book_id)

    if not book:
        return jsonify({"msg": "Book not found", "hostname": HOST_NAME}), 404

    if book.available_copies <= 0:
        return jsonify({"msg": "No copies available", "hostname": HOST_NAME}), 400

    # Create a borrowing record
    return_by = datetime.utcnow() + timedelta(days=14)  # Set the return by date to 14 days from now
    borrowing = Borrowing(book_id=book.id, user_id=user_id, return_by=return_by)

    # Decrease the available copies of the book
    book.available_copies -= 1

    # Save the changes
    db.session.add(borrowing)
    db.session.commit()

    # TODO: Send borrow_book message to RabbitMQ
    # send_borrow_message(user_id, book.id)

    return jsonify({
        "msg": "Book borrowed successfully",
        "hostname": HOST_NAME,
        "book": book.title,
        "user_id": user_id,
        "return_by": return_by
    }), 200