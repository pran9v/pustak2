import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bookexchange.db'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size