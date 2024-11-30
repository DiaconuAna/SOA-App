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
    quantity = data.get('quantity', 1)

    if not title or not author or not isbn:
        return jsonify({"msg": "Title, author and ISBN are required"}), 400

    # Ensure the ISBN is unique (optional validation)
    existing_book = Book.query.filter_by(isbn=isbn).first()
    if existing_book:
        return jsonify({"msg": "Book with this ISBN already exists"}), 400

    new_book = Book(title=title, author=author, isbn=isbn, available_copies=quantity)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"msg": "Book added successfully"}), 201
