from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, Blueprint
from app.models import db, User

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