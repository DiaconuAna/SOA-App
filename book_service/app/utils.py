from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt, jwt_required

import logging

def role_required(required_role):
    """
    Decorator to restrict access to users with a specific role.
    :param required_role: The role required to access the route.
    """
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            current_app.logger.debug(f"JWT Claims: {claims}")
            if str(claims.get('role')) != required_role:
                return jsonify({"msg": f"Access denied: {required_role} role required"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator
