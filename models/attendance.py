from datetime import datetime, date
from database.db import db


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    student_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    attendance_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Present') # Present, Late, Absent
    confidence = db.Column(db.Float, default=0.0)
    session_name = db.Column(db.String(50), default='Morning Session')
    verification_method = db.Column(db.String(30), default='Face Recognition')
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'attendance_date', 'session_name', name='unique_student_date_session'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'department': self.department,
            'attendance_date': self.attendance_date.strftime('%Y-%m-%d'),
            'attendance_time': self.attendance_time.strftime('%H:%M:%S'),
            'status': self.status,
            'confidence': round(self.confidence * 100, 1) if self.confidence else 0.0,
            'session_name': self.session_name,
            'verification_method': self.verification_method,
            'remarks': self.remarks,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
