import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()


def init_db_app(app):
    """Initialize database connection with MySQL, falling back to SQLite if needed."""
    use_mysql = Config.USE_MYSQL
    configured_uri = Config.MYSQL_URI if use_mysql else Config.SQLITE_URI
    
    if use_mysql:
        try:
            logger.info("Attempting to connect to MySQL database...")
            # Test direct connection
            engine = create_engine(Config.MYSQL_URI, connect_args={'connect_timeout': 3})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(" Successfully connected to MySQL database.")
            app.config['SQLALCHEMY_DATABASE_URI'] = Config.MYSQL_URI
            app.config['DB_TYPE'] = 'mysql'
        except Exception as e:
            logger.warning(f" Could not connect to MySQL ({e}). Falling back to local SQLite database.")
            app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLITE_URI
            app.config['DB_TYPE'] = 'sqlite'
    else:
        logger.info("Using SQLite database as configured.")
        app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLITE_URI
        app.config['DB_TYPE'] = 'sqlite'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Import models so tables are registered with metadata
        from models.user import User
        from models.student import Student
        from models.attendance import Attendance
        from models.settings import SystemSetting
        from models.activity_log import ActivityLog
        
        # Create all tables if they don't exist
        db.create_all()
        logger.info("Database tables verified / created.")
        
        # Seed default admin user and default system settings
        seed_default_data()


def seed_default_data():
    """Seed default administrator and system settings if not already present."""
    from models.user import User
    from models.settings import SystemSetting
    
    # Check for default admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@attendance.system',
            full_name='Master Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        logger.info("Default admin user created: admin / admin123")
        
    # Default settings
    default_settings = [
        ('recognition_threshold', str(Config.RECOGNITION_THRESHOLD), 'Confidence threshold for face recognition'),
        ('camera_index', str(Config.DEFAULT_CAMERA_INDEX), 'Default camera index (0 for built-in webcam)'),
        ('attendance_session', Config.ATTENDANCE_SESSION_NAME, 'Active attendance session name'),
        ('session_start_time', Config.SESSION_START_TIME, 'Session start time (HH:MM)'),
        ('session_late_time', Config.SESSION_LATE_TIME, 'Session late cutoff time (HH:MM)'),
        ('session_end_time', Config.SESSION_END_TIME, 'Session end time (HH:MM)'),
        ('cooldown_seconds', str(Config.ATTENDANCE_COOLDOWN_SECONDS), 'Seconds before same face can be logged again')
    ]
    
    for key, value, desc in default_settings:
        if not SystemSetting.query.filter_by(setting_key=key).first():
            setting = SystemSetting(setting_key=key, setting_value=value, description=desc)
            db.session.add(setting)
            
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding default data: {e}")
