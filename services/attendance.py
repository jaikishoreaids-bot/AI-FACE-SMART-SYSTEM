import time
import logging
from datetime import datetime, date, time as dtime
from database.db import db
from models.attendance import Attendance
from models.student import Student
from models.settings import SystemSetting
from models.activity_log import ActivityLog
from config import Config

logger = logging.getLogger(__name__)


class AttendanceService:
    """
    Core business logic for automatic attendance recording,
    duplicate prevention, session time tracking, and statistics.
    """
    
    # In-memory cooldown cache: student_id -> last_marked_timestamp
    _recent_marks = {}
    
    @classmethod
    def record_attendance(cls, student_id, confidence, session_name=None, verification_method="Face Recognition"):
        """
        Record attendance for a recognized student.
        Prevents duplicates on the same date and session.
        Returns (success: bool, status_message: str, attendance_dict: dict, was_duplicate: bool)
        """
        current_time_sec = time.time()
        cooldown_limit = int(SystemSetting.get_value('cooldown_seconds', Config.ATTENDANCE_COOLDOWN_SECONDS))
        
        # Check in-memory fast cooldown to prevent high-frequency hammering
        last_marked = cls._recent_marks.get(student_id, 0)
        if (current_time_sec - last_marked) < cooldown_limit:
            return False, f"Cooldown active for student {student_id}", None, True

        student = Student.query.filter_by(student_id=student_id, is_active=True).first()
        if not student:
            return False, f"Student ID '{student_id}' not found or inactive.", None, False

        today = date.today()
        now_time = datetime.now().time()
        
        if not session_name:
            session_name = SystemSetting.get_value('attendance_session', Config.ATTENDANCE_SESSION_NAME)

        # Check database for existing attendance entry today in this session
        existing = Attendance.query.filter_by(
            student_id=student_id,
            attendance_date=today,
            session_name=session_name
        ).first()

        if existing:
            # Update cache to suppress repeated notifications
            cls._recent_marks[student_id] = current_time_sec
            return True, f"Attendance already recorded today for {student.name} ({student_id})", existing.to_dict(), True

        # Determine Late vs Present based on configured session_late_time
        late_time_str = SystemSetting.get_value('session_late_time', Config.SESSION_LATE_TIME)
        try:
            late_h, late_m = map(int, late_time_str.split(':'))
            cutoff = dtime(late_h, late_m)
            status = "Late" if now_time > cutoff else "Present"
        except Exception:
            status = "Present"

        # Create new attendance record
        record = Attendance(
            student_id=student.student_id,
            student_name=student.name,
            department=student.department,
            attendance_date=today,
            attendance_time=now_time,
            status=status,
            confidence=confidence,
            session_name=session_name,
            verification_method=verification_method,
            remarks=f"Auto marked via {verification_method} (Confidence: {round(confidence * 100, 1)}%)"
        )

        try:
            db.session.add(record)
            db.session.commit()
            
            # Update cooldown timestamp
            cls._recent_marks[student_id] = current_time_sec
            
            # Log activity
            ActivityLog.log(
                event_type="ATTENDANCE_MARKED",
                description=f"Marked {status} for {student.name} ({student.student_id}) - {student.department}",
                student_id=student.student_id
            )
            
            logger.info(f"Attendance recorded: {student.name} ({student.student_id}) as {status} [{round(confidence*100, 1)}%]")
            return True, f"Attendance marked for {student.name} ({student.student_id})", record.to_dict(), False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record attendance: {e}")
            return False, f"Database error: {str(e)}", None, False

    @classmethod
    def get_today_summary(cls, target_date=None):
        """
        Calculate summary metrics for today (or specified date):
        Total Students, Present, Absent, Late, Attendance Rate (%).
        """
        if target_date is None:
            target_date = date.today()
            
        total_students = Student.query.filter_by(is_active=True).count()
        
        today_records = Attendance.query.filter_by(attendance_date=target_date).all()
        present_count = sum(1 for r in today_records if r.status in ('Present', 'Late'))
        late_count = sum(1 for r in today_records if r.status == 'Late')
        absent_count = max(0, total_students - present_count)
        
        rate = round((present_count / total_students * 100), 1) if total_students > 0 else 0.0
        
        # Recent live recognitions today (sorted newest first)
        recent_records = Attendance.query.filter_by(attendance_date=target_date)\
            .order_by(Attendance.attendance_time.desc()).limit(10).all()
            
        # Department breakdown for today
        dept_stats = {}
        for r in today_records:
            dept_stats[r.department] = dept_stats.get(r.department, 0) + 1
            
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'attendance_rate': rate,
            'department_breakdown': dept_stats,
            'recent_attendance': [r.to_dict() for r in recent_records]
        }

    @classmethod
    def get_student_attendance_stats(cls, student_id):
        """Calculate complete attendance stats for a specific student."""
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return None
            
        # Unique days with attendance
        total_present = Attendance.query.filter_by(student_id=student_id).filter(Attendance.status.in_(['Present', 'Late'])).count()
        total_late = Attendance.query.filter_by(student_id=student_id, status='Late').count()
        
        # Days since student enrolled
        start_date = student.created_at.date() if student.created_at else date.today()
        days_passed = max(1, (date.today() - start_date).days + 1)
        
        # Estimated total working days
        total_possible_days = Attendance.query.with_entities(Attendance.attendance_date).distinct().count()
        if total_possible_days == 0:
            total_possible_days = 1
            
        total_absent = max(0, total_possible_days - total_present)
        rate = round((total_present / total_possible_days * 100), 1) if total_possible_days > 0 else 0.0
        
        history = Attendance.query.filter_by(student_id=student_id)\
            .order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
            
        return {
            'student': student.to_dict(),
            'total_possible_days': total_possible_days,
            'present_days': total_present,
            'late_days': total_late,
            'absent_days': total_absent,
            'attendance_percentage': rate,
            'history': [h.to_dict() for h in history]
        }
