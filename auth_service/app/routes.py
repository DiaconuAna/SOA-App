from flask import Blueprint, request, jsonify
from app.models import User
from app.extensions import db
from app.services import create_jwt_token, hash_password, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username is None or password is None:
        return jsonify({"msg":"Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return jsonify({"msg":"Username already exists"}), 400

    password_hash = hash_password(password)
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg":"User created successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({"msg":"Invalid credentials"}), 401

    token = create_jwt_token(user)
    return jsonify({"msg":"Login successful", "access_token":token}), 200