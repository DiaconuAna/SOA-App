from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from . import db  # Assuming 'db' is initialized

class Book(db.Model):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(13), unique=True, nullable=False)
    available_copies = Column(Integer, default=1)

    # Relationship with Borrowing (1-to-many)
    borrowings = db.relationship("Borrowing", back_populates="book", cascade="all, delete-orphan")

    def __init__(self, title, author, isbn, available_copies=1):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.available_copies = available_copies

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class Borrowing(db.Model):
    __tablename__ = 'borrowings'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    borrowed_on = Column(DateTime, default=datetime.utcnow)
    return_by = Column(DateTime, nullable=True)
    returned_on = Column(DateTime, nullable=True)

    # Relationship to Book
    book = relationship("Book", back_populates="borrowings")
    # Relationship to User (assumes User table already exists in the User Service)
    # todo - removed for now until user service is created
    # user = relationship("User", back_populates="borrowed_books")

    # def __init__(self, book_id, user_id, return_by):
    def __init__(self, book_id, return_by):
        self.book_id = book_id
        # self.user_id = user_id
        self.return_by = return_by

    def __repr__(self):
        return f'<Borrowing {self.book.title} by {self.user.username}>'
