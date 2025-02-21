import queue

from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, Blueprint, request
from app.models import db, User
from app.utils import role_required
from app.broker import send_borrow_request, send_return_request
from app.cache import borrow_response_cache, return_response_cache


user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user = User.query.get(user_id)

    if not user:
        user = User(
                    role=claims.get('role'),
                    name=claims.get('name'),
                    username=claims.get('username')
                    )
        db.session.add(user)
        db.session.commit()

    return jsonify({
        "id": user.id,
        "role": user.role,
        "name": user.name,
        "username": user.username
    })

@user_bp.route('/borrow', methods=['POST'])
@role_required('user')  # Ensure the user is logged in
def borrow_book():
    data = request.get_json()
    user_id = int(data.get('user_id'))
    book_id = data.get('book_id')

    if not user_id or not book_id:
        return jsonify({"msg": "User ID and Book ID are required"}), 400

    # After validation, the user sends a message to RabbitMQ to process the borrowing.
    send_borrow_request(user_id, book_id)

    response = None
    attempts = 0
    while attempts < 10:
        try:
            response = borrow_response_cache.get(timeout=2)  # Wait for up to 2 seconds
            break
        except queue.Empty:
            attempts += 1
            continue

    if not response:
        return jsonify({"msg": "Request timed out, please try again later."}), 408  # Timeout if no response

    # Handle response based on status
    if response['status'] == 'success':
        return jsonify({"msg": response['message']}), 200  # Borrow successful
    elif response['status'] == 'failure':
        if "not found" in response['message']:
            return jsonify({"msg": response['message']}), 404  # Book not found
        elif "No copies available" in response['message']:
            return jsonify({"msg": response['message']}), 200  # No copies available
        elif "already borrowed" in response['message']:
            return jsonify({"msg": response['message']}), 409  # Book already borrowed
        else:
            return jsonify({"msg": response['message']}), 500  # Unexpected error
    else:
        # Catch-all for unexpected status
        return jsonify({"msg": "An unexpected error occurred"}), 500


@user_bp.route('/return', methods=['POST'])
@role_required('user')  # Ensure the user is logged in
def return_book():
    data = request.get_json()
    user_id = int(data.get('user_id'))
    book_id = data.get('book_id')

    if not user_id or not book_id:
        return jsonify({"msg": "User ID and Book ID are required"}), 400

    # Send return request to Book Service
    send_return_request(user_id, book_id)

    response = None
    attempts = 0
    while attempts < 10:
        try:
            response = return_response_cache.get(timeout=2)  # Wait for up to 2 seconds
            break
        except queue.Empty:
            attempts += 1
            continue

    if not response:
        return jsonify({"msg": "Request timed out, please try again later."}), 408  # Timeout if no response

    # Handle response based on status
    if response['status'] == 'success':
        return jsonify({"msg": response['message']}), 200  # Borrow successful
    elif response['status'] == 'failure':
            return jsonify({"msg": response['message']}), 500  # Unexpected error
    else:
        # Catch-all for unexpected status
        return jsonify({"msg": "An unexpected error occurred"}), 500

@user_bp.route('/users', methods=['GET'])
@role_required('librarian')  # Ensure the user has the 'librarian' role
def get_all_users():
    """
    Route for librarians to fetch a list of all users with their username, name, and ID.
    """
    users = User.query.all()

    if not users:
        return jsonify({"msg": "No users found"}), 404

    user_list = [
        {"id": user.id, "username": user.username, "name": user.name, "role": user.role}
        for user in users
    ]

    return jsonify({"users": user_list}), 200
