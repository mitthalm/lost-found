import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///campus_lostfound.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Matching algorithm thresholds
    MATCH_THRESHOLD = 0.3
    CATEGORY_BONUS = 0.3
    IMAGE_BONUS = 0.2
    IMAGE_HASH_THRESHOLD = 10
    
    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your_app_password_here'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'your_email@gmail.com'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@campus.edu'

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # Apple OAuth
    APPLE_CLIENT_ID = os.environ.get('APPLE_CLIENT_ID', '')
    APPLE_TEAM_ID = os.environ.get('APPLE_TEAM_ID', '')
    APPLE_KEY_ID = os.environ.get('APPLE_KEY_ID', '')
    APPLE_PRIVATE_KEY = os.environ.get('APPLE_PRIVATE_KEY', '')

    # Twilio (Phone OTP)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    OTP_EXPIRY_SECONDS = 300
