import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_change_me')
    
    # Security Configurations
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    if FLASK_ENV == 'production':
        SESSION_COOKIE_SECURE = True
        REMEMBER_COOKIE_SECURE = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'broke_geniuses.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Stripe Keys
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static')
    PROFILE_PICS_DIR = os.path.join(UPLOAD_FOLDER, 'profile_pics')
    SERVICE_IMAGES_DIR = os.path.join(UPLOAD_FOLDER, 'service_images')
    REVIEW_IMAGES_DIR = os.path.join(UPLOAD_FOLDER, 'review_images')
    SESSION_FILES_DIR = os.path.join(UPLOAD_FOLDER, 'session_files')
    
    # Max file size limit: 2MB
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    
    # Allowed formats
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
