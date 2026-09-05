import os
import logging
from datetime import datetime, date, timedelta
import random
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from config import Config
from database.db import db, init_db_app
from services.face_recognition import face_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


def create_app():
    """Application Factory for AI Face Recognition Attendance System."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize directories
    Config.init_app(app)
    
    # Enable CORS
    CORS(app)
    
    # Initialize Database
    init_db_app(app)
    
    # Initialize SocketIO
    socketio.init_app(app)
    
    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.student_routes import student_bp
    from routes.live_routes import live_bp
    from routes.attendance_routes import attendance_bp
    from routes.reports_routes import reports_bp
    from routes.settings_routes import settings_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    
    # Preload student embeddings into memory cache
    with app.app_context():
        face_engine.reload_student_cache(app)

    # Global template context processor
    @app.context_processor
    def inject_global_data():
        return {
            'app_name': 'AI Face Attendance Management System',
            'current_year': datetime.now().year,
            'current_date_str': datetime.now().strftime('%d %b %Y')
        }

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # CLI command to seed demo students and attendance for demonstration
    @app.cli.command("seed-demo-data")
    def seed_demo_data():
        """Seed sample students and past attendance history for demo/presentation."""
        from models.student import Student
        from models.attendance import Attendance
        import numpy as np

        logger.info("Seeding demonstration data...")
        
        sample_students = [
            ("101", "Jai Kishore", "Computer Science & Engineering", "4th Year", "A", "jai.kishore@college.edu", "+91 9876543210"),
            ("102", "Ananya Sharma", "Computer Science & Engineering", "4th Year", "A", "ananya.s@college.edu", "+91 9876543211"),
            ("103", "Rahul Verma", "Information Technology", "3rd Year", "B", "rahul.v@college.edu", "+91 9876543212"),
            ("104", "Pooja Patel", "Electronics & Communication", "4th Year", "A", "pooja.p@college.edu", "+91 9876543213"),
            ("105", "Vikram Singh", "Mechanical Engineering", "3rd Year", "A", "vikram.s@college.edu", "+91 9876543214"),
            ("106", "Sneha Reddy", "Artificial Intelligence & DS", "2nd Year", "A", "sneha.r@college.edu", "+91 9876543215"),
            ("107", "Karthik Iyer", "Computer Science & Engineering", "4th Year", "B", "karthik.i@college.edu", "+91 9876543216"),
            ("108", "Meera Nambiar", "Artificial Intelligence & DS", "3rd Year", "A", "meera.n@college.edu", "+91 9876543217")
        ]

        created_students = []
        for sid, name, dept, yr, sec, email, phone in sample_students:
            student = Student.query.filter_by(student_id=sid).first()
            if not student:
                student = Student(
                    student_id=sid,
                    name=name,
                    department=dept,
                    year=yr,
                    section=sec,
                    email=email,
                    phone=phone
                )
                # Generate a normalized 128D synthetic biometric embedding for offline demonstration
                synthetic_emb = np.random.uniform(-1, 1, 128)
                synthetic_emb = (synthetic_emb / np.linalg.norm(synthetic_emb)).tolist()
                student.set_embeddings([synthetic_emb])
                
                db.session.add(student)
                created_students.append(student)
                
        db.session.commit()
        logger.info(f"Created {len(created_students)} demo students.")

        # Seed attendance for past 7 days
        all_students = Student.query.all()
        today = date.today()
        
        for i in range(7):
            past_date = today - timedelta(days=i)
            # Attend ~75-90% of students
            attending = random.sample(all_students, k=random.randint(int(len(all_students) * 0.65), len(all_students)))
            for stu in attending:
                existing = Attendance.query.filter_by(student_id=stu.student_id, attendance_date=past_date).first()
                if not existing:
                    rand_hour = random.randint(8, 9)
                    rand_min = random.randint(10, 50)
                    rand_sec = random.randint(10, 59)
                    status = "Present" if (rand_hour == 8 or (rand_hour == 9 and rand_min <= 30)) else "Late"
                    conf = round(random.uniform(0.88, 0.98), 3)
                    
                    att = Attendance(
                        student_id=stu.student_id,
                        student_name=stu.name,
                        department=stu.department,
                        attendance_date=past_date,
                        attendance_time=datetime.strptime(f"{rand_hour:02d}:{rand_min:02d}:{rand_sec:02d}", "%H:%M:%S").time(),
                        status=status,
                        confidence=conf,
                        session_name="Morning Session",
                        verification_method="Face Recognition",
                        remarks=f"Verified with AI Confidence {round(conf*100, 1)}%"
                    )
                    db.session.add(att)
                    
        db.session.commit()
        face_engine.reload_student_cache()
        logger.info("Demo attendance data seeded successfully.")

    return app


app = create_app()


# WebSocket real-time live attendance events
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected to real-time attendance socket.")
    emit('status', {'connected': True, 'server_time': datetime.now().strftime('%H:%M:%S')})


@socketio.on('ping_stream')
def handle_ping(data):
    emit('pong_stream', {'timestamp': datetime.now().strftime('%H:%M:%S')})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f"Starting AI Face Attendance Management Server on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
