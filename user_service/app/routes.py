from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, Blueprint, request
from app.models import db, User
from app.utils import role_required
from app.messaging import send_borrow_request

from flask import current_app

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

    current_app.logger.info(f"Hey?")
    # After validation, the user sends a message to RabbitMQ to process the borrowing.
    send_borrow_request(user_id, book_id)

    return jsonify({"msg": "Borrow request sent"}), 200
