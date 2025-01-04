from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from . import db

class Book(db.Model):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(13), unique=True, nullable=False)
    available_copies = Column(Integer, default=1)

    # Relationship with Borrowing (1-to-many)
    borrowings = db.relationship("Borrowing", back_populates="book", cascade="all, delete-orphan")
    waitinglist = db.relationship("WaitingList", back_populates="book", cascade="all, delete-orphan")

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
    user_id = Column(Integer, nullable=False)
    borrowed_on = Column(DateTime, default=datetime.utcnow)
    return_by = Column(DateTime, nullable=True)
    returned_on = Column(DateTime, nullable=True)
    # Optional field to track event processing status
    event_processed = Column(Integer, default=0)  # 0 = Not processed, 1 = Processed

    # Relationship to Book
    book = relationship("Book", back_populates="borrowings")

    def __init__(self, book_id, user_id, return_by):
        self.book_id = book_id
        self.user_id = user_id
        self.return_by = return_by

    def __repr__(self):
        return f'<Borrowing {self.book.title} by {self.user.username}>'

class WaitingList(db.Model):
    __tablename__ = 'waitinglist'

    id = Column(db.Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(db.String(50), default='waiting')  # 'waiting' or 'notified'
    book = relationship("Book", back_populates="waitinglist")

    def __init__(self, book_id, user_id):
        self.book_id = book_id
        self.user_id = user_id

    def __repr__(self):
        return f'<WaitingList for {self.book.title} by {self.user.username}>'
