import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///health_tracker.db')
    
    # Fix for Railway PostgreSQL URL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads/blood_tests'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5007/api/auth/google/callback')

    FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
    FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET')
    FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI', 'http://localhost:5007/api/auth/fitbit/callback')

    OURA_CLIENT_ID = os.getenv('OURA_CLIENT_ID')
    OURA_CLIENT_SECRET = os.getenv('OURA_CLIENT_SECRET')
    OURA_REDIRECT_URI = os.getenv('OURA_REDIRECT_URI', 'http://localhost:5007/api/auth/oura/callback')

    CLUE_CLIENT_ID = os.getenv('CLUE_CLIENT_ID')
    CLUE_CLIENT_SECRET = os.getenv('CLUE_CLIENT_SECRET')

    GOOGLE_DRIVE_CLIENT_ID = os.getenv('GOOGLE_DRIVE_CLIENT_ID')
    GOOGLE_DRIVE_CLIENT_SECRET = os.getenv('GOOGLE_DRIVE_CLIENT_SECRET')
    GOOGLE_DRIVE_REDIRECT_URI = os.getenv('GOOGLE_DRIVE_REDIRECT_URI', 'http://localhost:5007/api/auth/google-drive/callback')
    CLUE_REDIRECT_URI = os.getenv('CLUE_REDIRECT_URI', 'http://localhost:5007/api/auth/clue/callback')

    # User access control
    ALLOWED_EMAILS = os.getenv('ALLOWED_EMAILS')

