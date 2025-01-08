import re

from flask import Blueprint, request, jsonify
from app.models import User
from app.extensions import db
from app.services import create_jwt_token, hash_password, verify_password

from flask import current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')

    if username is None:
        return jsonify({"msg":"Username is required"}), 400

    # Restrict username to letters and numbers only
    if not re.match("^[a-zA-Z0-9]+$", username):
        return jsonify({"msg": "Username can only contain letters and numbers"}), 400

    # Restrict role to 'librarian' or 'user'
    if role not in ["librarian", "user"]:
        return jsonify({"msg": "Role must be 'librarian' or 'user'"}), 400

    if password is None:
            return jsonify({"msg":"Password is required"}), 400

    if name is None:
            return jsonify({"msg":"Name is required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return jsonify({"msg":"Username already exists"}), 400

    password_hash = hash_password(password)
    new_user = User(username=username, password_hash=password_hash, name=name, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg":"User created successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    current_app.logger.info("Data is %s", data)
    current_app.logger.info("Username: %s, password: %s", username,  password)

    user = User.query.filter_by(username=username).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({"msg":"Invalid credentials"}), 401

    token = create_jwt_token(user)
    return jsonify({"msg":"Login successful", "access_token":token}), 200