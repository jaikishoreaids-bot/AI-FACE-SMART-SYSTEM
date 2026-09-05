import cv2
import base64
import numpy as np
import threading
import logging
from config import Config

logger = logging.getLogger(__name__)


class VideoCamera:
    """
    Thread-safe OpenCV Webcam Video Stream Capture with recognition HUD overlay.
    """
    def __init__(self, camera_index=None):
        self.camera_index = camera_index if camera_index is not None else Config.DEFAULT_CAMERA_INDEX
        self.video = None
        self.is_running = False
        self.lock = threading.Lock()
        self.latest_frame = None
        self.thread = None

    def start(self):
        with self.lock:
            if not self.is_running:
                try:
                    self.video = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
                    if not self.video.isOpened():
                        # Try default index 0
                        self.video = cv2.VideoCapture(0)
                        
                    if self.video.isOpened():
                        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.video.set(cv2.CAP_PROP_FPS, 30)
                        self.is_running = True
                        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
                        self.thread.start()
                        logger.info(f"Camera {self.camera_index} initialized successfully.")
                    else:
                        logger.warning(f"Could not open camera device {self.camera_index}.")
                except Exception as e:
                    logger.error(f"Error starting camera: {e}")

    def _capture_loop(self):
        while self.is_running:
            if self.video and self.video.isOpened():
                success, frame = self.video.read()
                if success:
                    with self.lock:
                        self.latest_frame = frame
            cv2.waitKey(15)

    def read_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                return True, self.latest_frame.copy()
            return False, None

    def stop(self):
        with self.lock:
            self.is_running = False
            if self.video and self.video.isOpened():
                self.video.release()
                self.video = None
        logger.info("Camera released.")


def decode_base64_image(base64_str):
    """Decode a base64 data URI string into an OpenCV BGR numpy image."""
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',', 1)[1]
        img_bytes = base64.b64decode(base64_str)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        return None


def encode_image_to_base64(image_bgr):
    """Encode an OpenCV BGR numpy image to base64 data URI string."""
    try:
        success, buffer = cv2.imencode('.jpg', image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not success:
            return None
        b64_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        return None


def draw_hud_overlay(frame, recognition_results):
    """
    Draw professional high-tech bounding box and recognition tag on frame.
    """
    annotated = frame.copy()
    
    for res in recognition_results:
        box = res.get('box', [0, 0, 0, 0])
        x, y, w, h = box
        matched = res.get('matched', False)
        name = res.get('name', 'Unknown')
        student_id = res.get('student_id', '')
        conf_pct = res.get('confidence_pct', 0)
        
        # Colors (BGR)
        color = (34, 197, 94) if matched else (59, 130, 246) # Green if recognized, Blue/Amber if unknown
        accent_color = (16, 185, 129) if matched else (239, 68, 68)
        
        # Bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        
        # Tech corner accents
        corner_len = min(20, w // 4, h // 4)
        thickness = 3
        # Top-Left
        cv2.line(annotated, (x, y), (x + corner_len, y), accent_color, thickness)
        cv2.line(annotated, (x, y), (x, y + corner_len), accent_color, thickness)
        # Top-Right
        cv2.line(annotated, (x + w, y), (x + w - corner_len, y), accent_color, thickness)
        cv2.line(annotated, (x + w, y), (x + w, y + corner_len), accent_color, thickness)
        # Bottom-Left
        cv2.line(annotated, (x, y + h), (x + corner_len, y + h), accent_color, thickness)
        cv2.line(annotated, (x, y + h), (x, y + h - corner_len), accent_color, thickness)
        # Bottom-Right
        cv2.line(annotated, (x + w, y + h), (x + w - corner_len, y + h), accent_color, thickness)
        cv2.line(annotated, (x + w, y + h), (x + w, y + h - corner_len), accent_color, thickness)
        
        # Header Label Badge
        if matched:
            label = f"{name} ({student_id}) - {conf_pct}%"
        else:
            label = f"Unknown ({conf_pct}%)"
            
        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.55, 1)
        bg_y1 = max(0, y - text_h - 10)
        bg_y2 = y
        cv2.rectangle(annotated, (x, bg_y1), (x + text_w + 12, bg_y2), (15, 23, 42), -1)
        cv2.rectangle(annotated, (x, bg_y1), (x + text_w + 12, bg_y2), color, 1)
        cv2.putText(annotated, label, (x + 6, y - 6), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    return annotated
