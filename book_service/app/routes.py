from flask import Blueprint, request, jsonify
from app.models import Book, db
from app.utils import role_required

book_bp = Blueprint('book', __name__)

@book_bp.route('/add', methods=['POST'])
@role_required('librarian')
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    available_copies = data.get('available_copies', 1)

    if not title or not author or not isbn:
        return jsonify({"msg": "Title, author and ISBN are required"}), 400

    # Ensure the ISBN is unique (optional validation)
    existing_book = Book.query.filter_by(isbn=isbn).first()
    if existing_book:
        return jsonify({"msg": "Book with this ISBN already exists"}), 400

    new_book = Book(title=title, author=author, isbn=isbn, available_copies=available_copies)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"msg": "Book added successfully"}), 201

@book_bp.route('/all_books', methods=['GET'])
@role_required('librarian', 'user')
def get_all_books():
    try:
        books = Book.query.all()

        if not books:
            return jsonify({"msg": "No books found"}), 404

        book_list = [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "available_copies": book.available_copies
            } for book in books]

        return jsonify({"books": book_list}), 200

    except Exception as e:
        return jsonify({"msg": f"Error retrieving books: {str(e)}"}), 500
