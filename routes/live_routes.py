import time
import cv2
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, Response, current_app
from routes.auth_routes import login_required
from services.face_recognition import face_engine
from services.attendance import AttendanceService
from services.camera import decode_base64_image, draw_hud_overlay, VideoCamera
from models.settings import SystemSetting
from models.student import Student

live_bp = Blueprint('live', __name__)

# Global camera instance for hardware stream mode
hardware_camera = None


@live_bp.route('/live')
@login_required
def live_view():
    threshold = float(SystemSetting.get_value('recognition_threshold', 0.65))
    session_name = SystemSetting.get_value('attendance_session', 'Morning Session')
    total_students = Student.query.filter_by(is_active=True).count()
    return render_template(
        'live_attendance.html',
        threshold=threshold,
        session_name=session_name,
        total_students=total_students
    )


@live_bp.route('/api/live/process_frame', methods=['POST'])
@login_required
def api_process_frame():
    """
    Process incoming client webcam frame:
    1. Detect all faces
    2. Extract embeddings & match against enrolled database
    3. If recognized with confidence >= threshold: automatically record attendance
    4. Return rich bounding boxes, recognition payload, and audio cue trigger
    """
    data = request.get_json() or {}
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'success': False, 'message': 'No image frame provided'}), 400
        
    custom_threshold = data.get('threshold')
    threshold = float(custom_threshold) if custom_threshold is not None else float(SystemSetting.get_value('recognition_threshold', 0.65))
    
    frame = decode_base64_image(image_b64)
    if frame is None:
        return jsonify({'success': False, 'message': 'Could not decode image'}), 400
        
    start_t = time.time()
    results, _ = face_engine.process_frame(frame, threshold=threshold)
    proc_time_ms = round((time.time() - start_t) * 1000, 1)
    
    processed_faces = []
    attendance_events = []
    
    for res in results:
        matched = res.get('matched', False)
        student_id = res.get('student_id')
        name = res.get('name')
        conf = res.get('confidence', 0.0)
        
        att_event = None
        if matched and student_id:
            # Auto-mark attendance
            ok, msg, record, was_duplicate = AttendanceService.record_attendance(
                student_id=student_id,
                confidence=conf,
                verification_method="Face Recognition"
            )
            
            att_event = {
                'student_id': student_id,
                'name': name,
                'department': res.get('department'),
                'confidence': res.get('confidence_pct'),
                'was_duplicate': was_duplicate,
                'message': msg,
                'record': record,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            attendance_events.append(att_event)
            
        face_entry = {
            'box': res.get('box'),
            'matched': matched,
            'status': res.get('status'),
            'student_id': student_id,
            'name': name,
            'department': res.get('department'),
            'year': res.get('year'),
            'section': res.get('section'),
            'confidence': res.get('confidence'),
            'confidence_pct': res.get('confidence_pct'),
            'photo_path': res.get('photo_path'),
            'attendance_event': att_event
        }
        processed_faces.append(face_entry)

    # Fetch updated today summary
    today_summary = AttendanceService.get_today_summary()

    return jsonify({
        'success': True,
        'faces': processed_faces,
        'faces_detected': len(processed_faces),
        'attendance_events': attendance_events,
        'processing_time_ms': proc_time_ms,
        'today_summary': {
            'present_count': today_summary['present_count'],
            'absent_count': today_summary['absent_count'],
            'attendance_rate': today_summary['attendance_rate'],
            'total_students': today_summary['total_students'],
            'recent_attendance': today_summary['recent_attendance']
        }
    })


def generate_mjpeg_frames(camera):
    """Generator for streaming server-side OpenCV camera feed."""
    while True:
        success, frame = camera.read_frame()
        if not success or frame is None:
            time.sleep(0.03)
            continue
            
        threshold = float(SystemSetting.get_value('recognition_threshold', 0.65))
        results, _ = face_engine.process_frame(frame, threshold=threshold)
        
        for res in results:
            if res.get('matched') and res.get('student_id'):
                AttendanceService.record_attendance(
                    student_id=res['student_id'],
                    confidence=res.get('confidence', 0.0)
                )
                
        annotated = draw_hud_overlay(frame, results)
        ret, jpeg = cv2.imencode('.jpg', annotated)
        if not ret:
            continue
            
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@live_bp.route('/video_feed')
@login_required
def video_feed():
    """Hardware OpenCV webcam MJPEG stream endpoint."""
    global hardware_camera
    cam_index = int(SystemSetting.get_value('camera_index', 0))
    if hardware_camera is None or not hardware_camera.is_running:
        hardware_camera = VideoCamera(cam_index)
        hardware_camera.start()
        
    return Response(
        generate_mjpeg_frames(hardware_camera),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
