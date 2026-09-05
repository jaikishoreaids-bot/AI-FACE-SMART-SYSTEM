from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func
from routes.auth_routes import login_required
from models.attendance import Attendance
from models.student import Student
from database.db import db

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def reports_view():
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]
    return render_template('reports.html', departments=departments)


@reports_bp.route('/api/reports/analytics')
@login_required
def api_reports_analytics():
    period = request.args.get('period', '7days') # 7days, 30days, today, month
    department = request.args.get('department', 'ALL')
    
    today = date.today()
    if period == 'today':
        start_date = today
    elif period == '30days':
        start_date = today - timedelta(days=29)
    elif period == 'month':
        start_date = date(today.year, today.month, 1)
    else: # 7days
        start_date = today - timedelta(days=6)

    # 1. Total Active Students
    stu_query = Student.query.filter_by(is_active=True)
    if department != 'ALL':
        stu_query = stu_query.filter_by(department=department)
    total_students = stu_query.count()
    
    # 2. Daily Attendance Trend within period
    trend_query = db.session.query(
        Attendance.attendance_date,
        func.count(Attendance.id).label('present_count')
    ).filter(Attendance.attendance_date >= start_date)
    
    if department != 'ALL':
        trend_query = trend_query.filter(Attendance.department == department)
        
    trend_results = trend_query.group_by(Attendance.attendance_date).order_by(Attendance.attendance_date.asc()).all()
    
    # Build complete date map
    date_labels = []
    present_series = []
    absent_series = []
    
    curr = start_date
    trend_map = {r.attendance_date: r.present_count for r in trend_results}
    while curr <= today:
        d_str = curr.strftime('%b %d')
        date_labels.append(d_str)
        p_count = trend_map.get(curr, 0)
        present_series.append(p_count)
        absent_series.append(max(0, total_students - p_count))
        curr += timedelta(days=1)
        
    # 3. Department Breakdown (for period)
    dept_query = db.session.query(
        Attendance.department,
        func.count(Attendance.id).label('count')
    ).filter(Attendance.attendance_date >= start_date)\
     .group_by(Attendance.department).all()
     
    dept_labels = [r.department for r in dept_query]
    dept_counts = [r.count for r in dept_query]
    
    # 4. Overall Present vs Absent in current period
    total_attendances = sum(present_series)
    total_possible = total_students * len(date_labels)
    overall_absent = max(0, total_possible - total_attendances)
    avg_rate = round((total_attendances / total_possible * 100), 1) if total_possible > 0 else 0.0

    # 5. Student Wise Summary Table
    students = stu_query.all()
    student_summary = []
    for s in students:
        s_count = Attendance.query.filter(
            Attendance.student_id == s.student_id,
            Attendance.attendance_date >= start_date
        ).count()
        s_rate = round((s_count / len(date_labels) * 100), 1) if len(date_labels) > 0 else 0.0
        student_summary.append({
            'student_id': s.student_id,
            'name': s.name,
            'department': s.department,
            'year': s.year,
            'section': s.section,
            'present_days': s_count,
            'total_days': len(date_labels),
            'attendance_rate': s_rate
        })
        
    # Sort students by attendance rate descending
    student_summary.sort(key=lambda x: x['attendance_rate'], reverse=True)

    return jsonify({
        'period': period,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'total_students': total_students,
        'avg_attendance_rate': avg_rate,
        'trends': {
            'labels': date_labels,
            'present': present_series,
            'absent': absent_series
        },
        'departments': {
            'labels': dept_labels,
            'counts': dept_counts
        },
        'students_table': student_summary
    })


@reports_bp.route('/api/reports/print-summary')
@login_required
def print_summary():
    """Printable clean summary view."""
    today = date.today()
    attendances = Attendance.query.filter_by(attendance_date=today).order_by(Attendance.department, Attendance.student_name).all()
    total_students = Student.query.filter_by(is_active=True).count()
    present_count = len(attendances)
    
    return render_template(
        'print_report.html',
        attendances=attendances,
        today=today.strftime('%d %B %Y'),
        total_students=total_students,
        present_count=present_count,
        absent_count=max(0, total_students - present_count),
        rate=round((present_count / total_students * 100), 1) if total_students > 0 else 0.0
    )
