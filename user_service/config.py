# define settings: database connection URL, JWT secret key

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'aminad41@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'wbse iged pezl bgqz')
    MAIL_DEFAULT_SENDER = 'noreply@yourdomain.com'
