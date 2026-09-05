import os
import uuid
import cv2
import numpy as np
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from routes.auth_routes import login_required
from models.student import Student
from models.attendance import Attendance
from models.activity_log import ActivityLog
from services.face_recognition import face_engine
from services.attendance import AttendanceService
from services.camera import decode_base64_image
from database.db import db
from config import Config

student_bp = Blueprint('students', __name__)


@student_bp.route('/students')
@login_required
def students_view():
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]
    return render_template('students.html', departments=departments)


@student_bp.route('/register')
@login_required
def register_view():
    return render_template('register.html')


@student_bp.route('/student/<student_id>')
@login_required
def student_profile_view(student_id):
    stats = AttendanceService.get_student_attendance_stats(student_id)
    if not stats:
        flash(f"Student '{student_id}' not found.", "warning")
        return redirect(url_for('students.students_view'))
    return render_template('student_profile.html', stats=stats)


@student_bp.route('/api/students/list')
@login_required
def api_students_list():
    query = Student.query
    
    # Search
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) |
            (Student.student_id.ilike(f"%{search}%")) |
            (Student.email.ilike(f"%{search}%"))
        )
        
    # Department filter
    department = request.args.get('department', '').strip()
    if department and department != 'ALL':
        query = query.filter(Student.department == department)
        
    # Year filter
    year = request.args.get('year', '').strip()
    if year and year != 'ALL':
        query = query.filter(Student.year == year)
        
    students = query.order_by(Student.created_at.desc()).all()
    return jsonify({
        'total': len(students),
        'students': [s.to_dict() for s in students]
    })


@student_bp.route('/api/students/validate-face', methods=['POST'])
@login_required
def api_validate_face():
    """AJAX real-time quality validator on a captured frame."""
    data = request.get_json() or {}
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'valid': False, 'message': 'No image provided'}), 400
        
    frame = decode_base64_image(image_b64)
    if frame is None:
        return jsonify({'valid': False, 'message': 'Invalid image format'}), 400
        
    faces = face_engine.detect_faces(frame)
    if len(faces) == 0:
        return jsonify({'valid': False, 'message': 'No face detected. Please face the camera.'})
    if len(faces) > 1:
        return jsonify({'valid': False, 'message': f'Multiple faces detected ({len(faces)}). Ensure only 1 person is in frame.'})
        
    box = faces[0]['box']
    is_valid, reason, metrics = face_engine.validate_face_quality(frame, box)
    
    return jsonify({
        'valid': is_valid,
        'message': reason,
        'metrics': metrics,
        'box': box
    })


@student_bp.route('/api/students/register', methods=['POST'])
@login_required
def api_register_student():
    """
    Register new student with personal details and multiple face captures.
    """
    data = request.get_json() or {}
    
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    year = data.get('year', '').strip()
    section = data.get('section', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    face_images = data.get('face_images', []) # List of base64 strings (3 to 5 images)
    
    # Validation
    if not (student_id and name and department and year and section and email):
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400
        
    if Student.query.filter_by(student_id=student_id).first():
        return jsonify({'success': False, 'message': f"Student ID '{student_id}' already exists."}), 400
        
    if Student.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': f"Email '{email}' is already registered."}), 400

    embeddings = []
    saved_photo_path = None
    
    # Process face captures
    if face_images and isinstance(face_images, list):
        for idx, img_b64 in enumerate(face_images):
            frame = decode_base64_image(img_b64)
            if frame is None:
                continue
                
            faces = face_engine.detect_faces(frame)
            if len(faces) == 1:
                raw_det = faces[0].get('raw_detection')
                emb = face_engine.extract_embedding(frame, raw_det)
                if emb is not None:
                    embeddings.append(emb)
                    
                # Save primary photo preview from first good sample
                if saved_photo_path is None:
                    photo_filename = f"{student_id}_{uuid.uuid4().hex[:8]}.jpg"
                    full_path = Config.STUDENT_PHOTOS_DIR / photo_filename
                    cv2.imwrite(str(full_path), frame)
                    saved_photo_path = f"/static/uploads/students/{photo_filename}"

    student = Student(
        student_id=student_id,
        name=name,
        department=department,
        year=year,
        section=section,
        email=email,
        phone=phone,
        photo_path=saved_photo_path
    )
    
    if embeddings:
        student.set_embeddings(embeddings)
        
    try:
        db.session.add(student)
        db.session.commit()
        
        # Reload memory cache
        face_engine.reload_student_cache()
        
        ActivityLog.log(
            'STUDENT_REGISTERED',
            f"Registered student {name} ({student_id}) with {len(embeddings)} face biometric samples.",
            student_id=student_id
        )
        
        return jsonify({
            'success': True,
            'message': f"Student {name} registered successfully with {len(embeddings)} face samples.",
            'student': student.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500


@student_bp.route('/api/students/<student_id>/update', methods=['POST'])
@login_required
def api_update_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
        
    data = request.get_json() or {}
    student.name = data.get('name', student.name).strip()
    student.department = data.get('department', student.department).strip()
    student.year = data.get('year', student.year).strip()
    student.section = data.get('section', student.section).strip()
    student.phone = data.get('phone', student.phone).strip()
    student.email = data.get('email', student.email).strip()
    
    # Check if new face embeddings were submitted
    face_images = data.get('face_images', [])
    if face_images:
        embeddings = []
        saved_photo_path = None
        for img_b64 in face_images:
            frame = decode_base64_image(img_b64)
            if frame is not None:
                faces = face_engine.detect_faces(frame)
                if len(faces) == 1:
                    raw_det = faces[0].get('raw_detection')
                    emb = face_engine.extract_embedding(frame, raw_det)
                    if emb is not None:
                        embeddings.append(emb)
                    if saved_photo_path is None:
                        photo_filename = f"{student_id}_{uuid.uuid4().hex[:8]}.jpg"
                        full_path = Config.STUDENT_PHOTOS_DIR / photo_filename
                        cv2.imwrite(str(full_path), frame)
                        saved_photo_path = f"/static/uploads/students/{photo_filename}"
        if embeddings:
            student.set_embeddings(embeddings)
            if saved_photo_path:
                student.photo_path = saved_photo_path

    try:
        db.session.commit()
        face_engine.reload_student_cache()
        ActivityLog.log('STUDENT_UPDATED', f"Updated record for {student.name} ({student_id})", student_id=student_id)
        return jsonify({'success': True, 'message': 'Student updated successfully.', 'student': student.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/<student_id>/delete-biometric', methods=['POST'])
@login_required
def api_delete_biometric(student_id):
    """Purges biometric face embedding data for GDPR / biometric privacy compliance."""
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
        
    student.set_embeddings(None)
    student.photo_path = None
    
    try:
        db.session.commit()
        face_engine.reload_student_cache()
        ActivityLog.log('BIOMETRIC_DELETED', f"Purged biometric data for student {student_id}", student_id=student_id)
        return jsonify({'success': True, 'message': f"Biometric data for student {student_id} has been permanently deleted."})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/students/<student_id>/delete', methods=['POST'])
@login_required
def api_delete_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
        
    try:
        name = student.name
        db.session.delete(student)
        db.session.commit()
        face_engine.reload_student_cache()
        ActivityLog.log('STUDENT_DELETED', f"Deleted student {name} ({student_id}) and associated records.")
        return jsonify({'success': True, 'message': f"Student {name} deleted successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
