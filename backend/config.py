import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}