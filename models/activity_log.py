from datetime import datetime
from database.db import db


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @classmethod
    def log(cls, event_type, description, student_id=None, ip_address=None):
        try:
            entry = cls(
                event_type=event_type,
                description=description,
                student_id=student_id,
                ip_address=ip_address
            )
            db.session.add(entry)
            db.session.commit()
            return entry
        except Exception:
            db.session.rollback()
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'description': self.description,
            'student_id': self.student_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'time_ago': self.created_at.strftime('%H:%M:%S')
        }
