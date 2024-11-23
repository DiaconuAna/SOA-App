from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Utility functions for Password and JWT tokens

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)

def create_jwt_token(user):
    return create_access_token(identity=user.id, expires_delta=datetime.timedelta(hours=1))
