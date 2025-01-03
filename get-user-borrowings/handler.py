import json
import psycopg2
import os
from datetime import datetime
import jwt

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
VALID_ROLES = ["librarian", "user"]


def get_user_borrowings(event, context):
    # Extract JWT token from the Authorization header
    authorization_header = event.get("headers", {}).get("Authorization", "")
    if not authorization_header:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Authorization token is required"})
        }

    # Token is in the form "Bearer <token>"
    token = authorization_header.split(" ")[1] if len(authorization_header.split(" ")) > 1 else None
    if not token:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Token not found in Authorization header"})
        }

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id_from_token = decoded_token.get("sub")
        role_from_token = decoded_token.get("role")

        if role_from_token not in VALID_ROLES:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Insufficient permissions"})
            }
    except jwt.ExpiredSignatureError:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Token has expired"})
        }
    except jwt.InvalidTokenError:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Invalid token"})
        }

    user_id = event.get("queryStringParameters", {}).get("user_id")

    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "user_id is required"})
        }

    # Database connection details from environment variables
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", 5434)

    try:
        # Connect to the database
        connection = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        cursor = connection.cursor()

        # Query to get borrowings for the user
        query = """
            SELECT b.title, br.borrowed_on, br.return_by
            FROM borrowings br
            JOIN books b ON br.book_id = b.id
            WHERE br.user_id = %s AND br.returned_on IS NULL;
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()

        borrowings = [
            {
                "title": row[0],
                "borrowed_on": row[1].isoformat() if isinstance(row[1], datetime) else row[1],
                "return_by": row[2].isoformat() if isinstance(row[2], datetime) else row[2]
            }
            for row in rows
        ]

        # Close connections
        cursor.close()
        connection.close()

        return {
            "statusCode": 200,
            "body": json.dumps(borrowings)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
