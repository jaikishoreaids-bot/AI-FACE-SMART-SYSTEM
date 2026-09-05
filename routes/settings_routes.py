import time
from flask import Blueprint, render_template, request, jsonify, session, current_app
from sqlalchemy import text
from routes.auth_routes import login_required
from models.user import User
from models.student import Student
from models.attendance import Attendance
from models.settings import SystemSetting
from models.activity_log import ActivityLog
from services.face_recognition import face_engine
from database.db import db
from config import Config

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@login_required
def settings_view():
    user = User.query.get(session.get('user_id'))
    threshold = float(SystemSetting.get_value('recognition_threshold', Config.RECOGNITION_THRESHOLD))
    camera_index = int(SystemSetting.get_value('camera_index', Config.DEFAULT_CAMERA_INDEX))
    attendance_session = SystemSetting.get_value('attendance_session', Config.ATTENDANCE_SESSION_NAME)
    session_start_time = SystemSetting.get_value('session_start_time', Config.SESSION_START_TIME)
    session_late_time = SystemSetting.get_value('session_late_time', Config.SESSION_LATE_TIME)
    session_end_time = SystemSetting.get_value('session_end_time', Config.SESSION_END_TIME)
    cooldown_seconds = int(SystemSetting.get_value('cooldown_seconds', Config.ATTENDANCE_COOLDOWN_SECONDS))
    
    return render_template(
        'settings.html',
        user=user,
        threshold=threshold,
        camera_index=camera_index,
        attendance_session=attendance_session,
        session_start_time=session_start_time,
        session_late_time=session_late_time,
        session_end_time=session_end_time,
        cooldown_seconds=cooldown_seconds,
        db_type=current_app.config.get('DB_TYPE', 'unknown')
    )


@settings_bp.route('/api/settings/update', methods=['POST'])
@login_required
def api_update_settings():
    data = request.get_json() or {}
    
    threshold = data.get('threshold')
    if threshold is not None:
        val = float(threshold)
        SystemSetting.set_value('recognition_threshold', str(val), 'Face recognition confidence threshold')
        Config.RECOGNITION_THRESHOLD = val
        
    camera_index = data.get('camera_index')
    if camera_index is not None:
        SystemSetting.set_value('camera_index', str(camera_index), 'Default camera index')
        
    attendance_session = data.get('attendance_session')
    if attendance_session:
        SystemSetting.set_value('attendance_session', str(attendance_session).strip(), 'Active attendance session name')
        
    session_start_time = data.get('session_start_time')
    if session_start_time:
        SystemSetting.set_value('session_start_time', str(session_start_time).strip())
        
    session_late_time = data.get('session_late_time')
    if session_late_time:
        SystemSetting.set_value('session_late_time', str(session_late_time).strip())
        
    session_end_time = data.get('session_end_time')
    if session_end_time:
        SystemSetting.set_value('session_end_time', str(session_end_time).strip())
        
    cooldown_seconds = data.get('cooldown_seconds')
    if cooldown_seconds is not None:
        SystemSetting.set_value('cooldown_seconds', str(cooldown_seconds))

    ActivityLog.log('SETTINGS_UPDATED', "System settings updated by administrator.")
    return jsonify({'success': True, 'message': 'System settings saved successfully.'})


@settings_bp.route('/api/settings/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    current_pass = data.get('current_password', '')
    new_pass = data.get('new_password', '')
    confirm_pass = data.get('confirm_password', '')
    
    if not (current_pass and new_pass and confirm_pass):
        return jsonify({'success': False, 'message': 'All password fields are required.'}), 400
        
    if new_pass != confirm_pass:
        return jsonify({'success': False, 'message': 'New passwords do not match.'}), 400
        
    if len(new_pass) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'}), 400
        
    user = User.query.get(session.get('user_id'))
    if not user or not user.check_password(current_pass):
        return jsonify({'success': False, 'message': 'Incorrect current password.'}), 400
        
    user.set_password(new_pass)
    try:
        db.session.commit()
        ActivityLog.log('PASSWORD_CHANGED', f"Password changed for user {user.username}")
        return jsonify({'success': True, 'message': 'Password updated successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/api/settings/db-health')
@login_required
def api_db_health():
    """Verify database connection health and statistics."""
    start_t = time.time()
    try:
        db.session.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_t) * 1000, 2)
        
        students_count = Student.query.count()
        enrolled_faces = Student.query.filter(Student.face_embedding.isnot(None)).count()
        attendance_count = Attendance.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database_type': current_app.config.get('DB_TYPE', 'Unknown'),
            'latency_ms': latency_ms,
            'students_count': students_count,
            'enrolled_faces': enrolled_faces,
            'attendance_records': attendance_count,
            'face_engine_ready': True,
            'onnx_engine_active': face_engine.use_onnx
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'database_type': current_app.config.get('DB_TYPE', 'Unknown')
        }), 500
