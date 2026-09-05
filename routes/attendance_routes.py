import io
import csv
from datetime import datetime, date
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, send_file, make_response
from routes.auth_routes import login_required
from models.attendance import Attendance
from models.student import Student
from models.activity_log import ActivityLog
from services.attendance import AttendanceService
from database.db import db

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/attendance')
@login_required
def attendance_view():
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]
    today_str = date.today().strftime('%Y-%m-%d')
    return render_template('attendance.html', departments=departments, today_str=today_str)


@attendance_bp.route('/api/attendance/list')
@login_required
def api_attendance_list():
    query = Attendance.query
    
    # Filter by Date
    date_filter = request.args.get('date', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    if date_filter:
        try:
            d = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date == d)
        except ValueError:
            pass
    elif start_date and end_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date.between(sd, ed))
        except ValueError:
            pass
            
    # Filter by Department
    department = request.args.get('department', '').strip()
    if department and department != 'ALL':
        query = query.filter(Attendance.department == department)
        
    # Filter by Status
    status = request.args.get('status', '').strip()
    if status and status != 'ALL':
        query = query.filter(Attendance.status == status)
        
    # Search by Student ID or Name
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            (Attendance.student_id.ilike(f"%{search}%")) |
            (Attendance.student_name.ilike(f"%{search}%"))
        )
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'per_page': per_page,
        'records': [r.to_dict() for r in pagination.items]
    })


@attendance_bp.route('/api/attendance/manual-mark', methods=['POST'])
@login_required
def api_manual_mark():
    data = request.get_json() or {}
    student_id = data.get('student_id', '').strip()
    status = data.get('status', 'Present').strip()
    session_name = data.get('session_name', 'Morning Session').strip()
    remarks = data.get('remarks', 'Manual entry by Admin').strip()
    
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'success': False, 'message': f"Student ID '{student_id}' not found."}), 404
        
    today = date.today()
    existing = Attendance.query.filter_by(
        student_id=student_id,
        attendance_date=today,
        session_name=session_name
    ).first()
    
    if existing:
        existing.status = status
        existing.remarks = remarks
        existing.verification_method = 'Manual Admin Override'
        db.session.commit()
        return jsonify({'success': True, 'message': f"Updated attendance for {student.name} to {status}.", 'record': existing.to_dict()})
        
    record = Attendance(
        student_id=student.student_id,
        student_name=student.name,
        department=student.department,
        attendance_date=today,
        attendance_time=datetime.now().time(),
        status=status,
        confidence=1.0,
        session_name=session_name,
        verification_method='Manual Admin Entry',
        remarks=remarks
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        ActivityLog.log('MANUAL_ATTENDANCE', f"Manually recorded {status} for {student.name} ({student_id})", student_id=student_id)
        return jsonify({'success': True, 'message': f"Attendance marked for {student.name}.", 'record': record.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@attendance_bp.route('/api/attendance/delete/<int:record_id>', methods=['POST'])
@login_required
def api_delete_attendance(record_id):
    record = Attendance.query.get(record_id)
    if not record:
        return jsonify({'success': False, 'message': 'Record not found.'}), 404
        
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Attendance record deleted.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@attendance_bp.route('/api/attendance/export/csv')
@login_required
def export_csv():
    """Export attendance data as CSV with active filters."""
    query = Attendance.query
    
    date_filter = request.args.get('date', '').strip()
    if date_filter:
        try:
            d = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date == d)
        except ValueError:
            pass
            
    department = request.args.get('department', '').strip()
    if department and department != 'ALL':
        query = query.filter(Attendance.department == department)
        
    records = query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Record ID', 'Student ID', 'Student Name', 'Department', 'Date', 'Time', 'Status', 'Confidence (%)', 'Session', 'Verification Method', 'Remarks'])
    
    for r in records:
        writer.writerow([
            r.id,
            r.student_id,
            r.student_name,
            r.department,
            r.attendance_date.strftime('%Y-%m-%d'),
            r.attendance_time.strftime('%H:%M:%S'),
            r.status,
            f"{round(r.confidence * 100, 1)}%" if r.confidence else 'N/A',
            r.session_name,
            r.verification_method,
            r.remarks or ''
        ])
        
    output.seek(0)
    filename = f"attendance_report_{date_filter or date.today().strftime('%Y%m%d')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@attendance_bp.route('/api/attendance/export/excel')
@login_required
def export_excel():
    """Export attendance data as Excel (.xlsx)."""
    query = Attendance.query
    date_filter = request.args.get('date', '').strip()
    if date_filter:
        try:
            d = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date == d)
        except ValueError:
            pass
            
    department = request.args.get('department', '').strip()
    if department and department != 'ALL':
        query = query.filter(Attendance.department == department)
        
    records = query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
    
    data = []
    for r in records:
        data.append({
            'Record ID': r.id,
            'Student ID': r.student_id,
            'Student Name': r.student_name,
            'Department': r.department,
            'Date': r.attendance_date.strftime('%Y-%m-%d'),
            'Time': r.attendance_time.strftime('%H:%M:%S'),
            'Status': r.status,
            'Confidence (%)': f"{round(r.confidence * 100, 1)}%" if r.confidence else 'N/A',
            'Session': r.session_name,
            'Method': r.verification_method,
            'Remarks': r.remarks or ''
        })
        
    df = pd.DataFrame(data)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance Records')
        
    excel_buffer.seek(0)
    filename = f"attendance_export_{date_filter or date.today().strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
