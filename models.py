from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    books = db.relationship('Book', backref='owner', lazy=True)
    interests = db.relationship('Interest', backref='user', lazy=True)
    # Exchange requests
    sent_requests = db.relationship('BookExchangeRequest',
                                  foreign_keys='BookExchangeRequest.requester_id',
                                  backref=db.backref('requester_user', lazy=True))
    received_requests = db.relationship('BookExchangeRequest',
                                      foreign_keys='BookExchangeRequest.owner_id',
                                      backref=db.backref('owner_user', lazy=True))

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    exchange_book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    book = db.relationship('Book', backref='interested_users', foreign_keys=[book_id])
    exchange_book = db.relationship('Book', foreign_keys=[exchange_book_id])

class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book1_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book2_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    user1_payment = db.Column(db.Boolean, default=False)
    user2_payment = db.Column(db.Boolean, default=False)
    payment_amount = db.Column(db.Float, default=25.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    book1 = db.relationship('Book', foreign_keys=[book1_id])
    book2 = db.relationship('Book', foreign_keys=[book2_id])
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])

class BookExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requested_book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    offered_book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Book relationships
    requested_book = db.relationship('Book', foreign_keys=[requested_book_id])
    offered_book = db.relationship('Book', foreign_keys=[offered_book_id])

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=True)  # New price field