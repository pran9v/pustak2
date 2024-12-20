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

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book1_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book2_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    user1_payment = db.Column(db.Boolean, default=False)
    user2_payment = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)