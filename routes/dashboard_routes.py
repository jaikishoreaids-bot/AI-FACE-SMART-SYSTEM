from datetime import datetime, date
from flask import Blueprint, render_template, jsonify, session, redirect, url_for, current_app
from routes.auth_routes import login_required
from services.attendance import AttendanceService
from models.student import Student
from models.attendance import Attendance
from models.activity_log import ActivityLog
from models.settings import SystemSetting

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    today = date.today()
    summary = AttendanceService.get_today_summary(today)
    active_session = SystemSetting.get_value('attendance_session', 'Morning Session')
    threshold = SystemSetting.get_value('recognition_threshold', '0.65')
    
    # Recent 5 activity logs
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    return render_template(
        'dashboard.html',
        summary=summary,
        active_session=active_session,
        threshold=threshold,
        recent_logs=[log.to_dict() for log in recent_logs],
        current_date=today.strftime('%A, %B %d, %Y'),
        current_time=datetime.now().strftime('%I:%M %p')
    )


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats_api():
    today = date.today()
    summary = AttendanceService.get_today_summary(today)
    
    # Add server time
    summary['server_time'] = datetime.now().strftime('%H:%M:%S')
    summary['server_date'] = today.strftime('%Y-%m-%d')
    
    return jsonify(summary)
