from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from . import db

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # Example: 'user' or 'librarian'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, username, name, role, is_active=True):
        self.username = username
        self.name = name
        self.role = role

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class WatchedBook(db.Model):
    __tablename__ = 'watched_books'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, nullable=False)  # Only store the book_id, no direct relationship
    watched_on = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ForeignKey added here

    # Relationship to User (Assumed already exists)
    user = db.relationship("User", backref="watched_books")

    def __repr__(self):
        return f'<WatchedBook {self.book_id} by {self.user.username}>'
