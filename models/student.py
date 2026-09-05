import json
from datetime import datetime
from database.db import db


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.String(20), nullable=False, index=True)
    section = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Store multiple face embedding vectors as JSON list of lists (e.g. 3-5 embeddings per student)
    face_embedding = db.Column(db.Text, nullable=True)
    samples_count = db.Column(db.Integer, default=0)
    photo_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    biometric_registered_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with attendance
    attendances = db.relationship('Attendance', backref='student_ref', lazy=True, cascade='all, delete-orphan')

    def set_embeddings(self, embeddings_list):
        """Save a list of float vectors as JSON string."""
        if embeddings_list is not None:
            # ensure serializable Python floats
            serializable = [
                [float(val) for val in emb] if hasattr(emb, '__iter__') else float(emb)
                for emb in embeddings_list
            ]
            self.face_embedding = json.dumps(serializable)
            self.samples_count = len(serializable)
            self.biometric_registered_at = datetime.utcnow()
        else:
            self.face_embedding = None
            self.samples_count = 0
            self.biometric_registered_at = None

    def get_embeddings(self):
        """Retrieve the list of embedding vectors as python lists."""
        if not self.face_embedding:
            return []
        try:
            return json.loads(self.face_embedding)
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'department': self.department,
            'year': self.year,
            'section': self.section,
            'email': self.email,
            'phone': self.phone,
            'has_biometric': bool(self.face_embedding),
            'samples_count': self.samples_count,
            'photo_path': self.photo_path,
            'is_active': self.is_active,
            'biometric_registered_at': self.biometric_registered_at.strftime('%Y-%m-%d %H:%M:%S') if self.biometric_registered_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
