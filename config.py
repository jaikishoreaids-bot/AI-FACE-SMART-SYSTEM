import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'ai_attendance_system_production_secret_key_2026')
    BASE_DIR = BASE_DIR
    
    # Upload directories
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    STUDENT_PHOTOS_DIR = UPLOAD_FOLDER / 'students'
    MODELS_DIR = BASE_DIR / 'models' / 'weights'
    
    # Database Settings
    USE_MYSQL = os.getenv('USE_MYSQL', 'True').lower() in ('true', '1', 't')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'ai_attendance_system')
    
    # Build database URI with fallback
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    SQLITE_URI = f"sqlite:///{BASE_DIR / 'database' / 'ai_attendance.db'}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Face Recognition Parameters
    RECOGNITION_THRESHOLD = float(os.getenv('RECOGNITION_THRESHOLD', 0.65))
    FACE_DETECTION_CONFIDENCE = float(os.getenv('FACE_DETECTION_CONFIDENCE', 0.60))
    FRAME_RESIZE_WIDTH = int(os.getenv('FRAME_RESIZE_WIDTH', 640))
    ANTI_SPOOF_CHECK = os.getenv('ANTI_SPOOF_CHECK', 'True').lower() in ('true', '1', 't')
    
    # Camera settings
    DEFAULT_CAMERA_INDEX = int(os.getenv('DEFAULT_CAMERA_INDEX', 0))
    
    # Session & Attendance Rules
    ATTENDANCE_SESSION_NAME = os.getenv('ATTENDANCE_SESSION_NAME', 'Morning Session')
    SESSION_START_TIME = os.getenv('SESSION_START_TIME', '08:00')
    SESSION_LATE_TIME = os.getenv('SESSION_LATE_TIME', '09:30')
    SESSION_END_TIME = os.getenv('SESSION_END_TIME', '17:00')
    ATTENDANCE_COOLDOWN_SECONDS = int(os.getenv('ATTENDANCE_COOLDOWN_SECONDS', 60))

    @classmethod
    def init_app(cls, app):
        """Ensure upload directories exist."""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.STUDENT_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        (cls.BASE_DIR / 'database').mkdir(parents=True, exist_ok=True)
