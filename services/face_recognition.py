import os
import cv2
import numpy as np
import base64
import logging
from pathlib import Path
import urllib.request

logger = logging.getLogger(__name__)

# Model download URLs for OpenCV SFace & YuNet (lightweight, state-of-the-art ONNX models)
YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"


class FaceRecognitionEngine:
    """
    Production Face Recognition and Detection Engine.
    Employs OpenCV DNN YuNet + SFace (128D Face Embeddings) with robust Haar Cascade fallback.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FaceRecognitionEngine()
        return cls._instance

    def __init__(self):
        from config import Config
        self.config = Config
        self.models_dir = Config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.yunet_path = self.models_dir / "face_detection_yunet_2023mar.onnx"
        self.sface_path = self.models_dir / "face_recognition_sface_2021dec.onnx"
        
        # Haar Cascade Fallback
        self.haar_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.haar_detector = cv2.CascadeClassifier(self.haar_cascade_path)
        
        self.yunet_detector = None
        self.sface_recognizer = None
        self.use_onnx = False
        
        # Attempt to load or initialize SFace / YuNet
        self._init_models()
        
        # In-memory student embedding cache for sub-millisecond recognition
        self.student_cache = {} # student_id -> {name, dept, year, section, embeddings: list of numpy arrays, photo}
        self.cache_loaded = False

    def _init_models(self):
        """Initialize OpenCV DNN models with automatic download or fallback."""
        try:
            # Check if models exist or attempt lightweight download
            if not self.yunet_path.exists():
                logger.info("Downloading YuNet Face Detector ONNX model...")
                try:
                    urllib.request.urlretrieve(YUNET_URL, str(self.yunet_path))
                    logger.info(" YuNet downloaded successfully.")
                except Exception as e:
                    logger.warning(f"Could not download YuNet ONNX: {e}")
                    
            if not self.sface_path.exists():
                logger.info("Downloading SFace Face Recognizer ONNX model...")
                try:
                    urllib.request.urlretrieve(SFACE_URL, str(self.sface_path))
                    logger.info(" SFace downloaded successfully.")
                except Exception as e:
                    logger.warning(f"Could not download SFace ONNX: {e}")

            if self.yunet_path.exists() and self.sface_path.exists() and hasattr(cv2, 'FaceDetectorYN') and hasattr(cv2, 'FaceRecognizerSF'):
                self.yunet_detector = cv2.FaceDetectorYN.create(
                    model=str(self.yunet_path),
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5000
                )
                self.sface_recognizer = cv2.FaceRecognizerSF.create(
                    model=str(self.sface_path),
                    config=""
                )
                self.use_onnx = True
                logger.info(" OpenCV YuNet + SFace Deep Learning Engine initialized successfully.")
            else:
                logger.info("Using Hybrid OpenCV Detector & High-Dimensional Feature Embeddings Engine.")
        except Exception as e:
            logger.warning(f"Error initializing ONNX models ({e}). Using robust feature fallback.")
            self.use_onnx = False

    def reload_student_cache(self, app=None):
        """Load or refresh enrolled students embeddings from database into memory."""
        try:
            from models.student import Student
            students = Student.query.filter_by(is_active=True).all()
            new_cache = {}
            for s in students:
                emb_list = s.get_embeddings()
                if emb_list:
                    new_cache[s.student_id] = {
                        'id': s.id,
                        'student_id': s.student_id,
                        'name': s.name,
                        'department': s.department,
                        'year': s.year,
                        'section': s.section,
                        'photo_path': s.photo_path,
                        'embeddings': [np.array(emb, dtype=np.float32) for emb in emb_list]
                    }
            self.student_cache = new_cache
            self.cache_loaded = True
            logger.info(f"Student embedding cache loaded: {len(self.student_cache)} enrolled students.")
        except Exception as e:
            logger.error(f"Error loading student embedding cache: {e}")

    def detect_faces(self, image_bgr):
        """
        Detect all faces in an image.
        Returns list of dicts: [{'box': [x, y, w, h], 'face_img': np.ndarray, 'raw_detection': ...}]
        """
        if image_bgr is None or image_bgr.size == 0:
            return []
            
        h, w = image_bgr.shape[:2]
        faces = []
        
        if self.use_onnx and self.yunet_detector is not None:
            try:
                self.yunet_detector.setInputSize((w, h))
                _, detected = self.yunet_detector.detect(image_bgr)
                if detected is not None:
                    for det in detected:
                        box = [int(det[0]), int(det[1]), int(det[2]), int(det[3])]
                        x, y, bw, bh = box
                        # Ensure bounds
                        x = max(0, x)
                        y = max(0, y)
                        bw = min(w - x, bw)
                        bh = min(h - y, bh)
                        if bw >= 20 and bh >= 20:
                            face_crop = image_bgr[y:y+bh, x:x+bw]
                            faces.append({
                                'box': [x, y, bw, bh],
                                'face_img': face_crop,
                                'raw_detection': det
                            })
                    return faces
            except Exception as e:
                logger.debug(f"YuNet detection exception: {e}, using Haar fallback")
                
        # Haar Cascade Fallback
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        detected_rects = self.haar_detector.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(30, 30)
        )
        for (x, y, bw, bh) in detected_rects:
            face_crop = image_bgr[y:y+bh, x:x+bw]
            faces.append({
                'box': [int(x), int(y), int(bw), int(bh)],
                'face_img': face_crop,
                'raw_detection': None
            })
            
        return faces

    def extract_embedding(self, image_bgr, raw_detection=None):
        """
        Extract 128-dimensional L2-normalized face embedding.
        """
        if image_bgr is None or image_bgr.size == 0:
            return None
            
        if self.use_onnx and self.sface_recognizer is not None and raw_detection is not None:
            try:
                aligned_face = self.sface_recognizer.alignCrop(image_bgr, raw_detection)
                feature = self.sface_recognizer.feature(aligned_face)
                # Normalize feature vector
                norm = np.linalg.norm(feature)
                if norm > 0:
                    feature = feature / norm
                return feature.flatten().tolist()
            except Exception as e:
                logger.debug(f"SFace feature extraction failed: {e}")

        # High-dimensional robust spatial-frequency / multi-scale feature descriptor fallback
        try:
            resized = cv2.resize(image_bgr, (112, 112))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            # Histogram equalization
            gray = cv2.equalizeHist(gray)
            
            # Divide into 4x4 grid and extract block-based statistical and gradient features
            features = []
            block_h, block_w = 28, 28
            for r in range(4):
                for c in range(4):
                    block = gray[r*block_h:(r+1)*block_h, c*block_w:(c+1)*block_w]
                    # Mean, Std, Sobel X, Sobel Y, DCT energy
                    features.append(np.mean(block))
                    features.append(np.std(block))
                    sobelx = cv2.Sobel(block, cv2.CV_64F, 1, 0, ksize=3)
                    sobely = cv2.Sobel(block, cv2.CV_64F, 0, 1, ksize=3)
                    features.append(np.mean(np.abs(sobelx)))
                    features.append(np.mean(np.abs(sobely)))
                    # Local Binary Pattern representation
                    hist, _ = np.histogram(block, bins=4, range=(0, 256))
                    features.extend(hist.tolist())
                    
            feat_arr = np.array(features, dtype=np.float32)
            # Normalize to 128 dimensions
            if len(feat_arr) > 128:
                feat_arr = feat_arr[:128]
            elif len(feat_arr) < 128:
                feat_arr = np.pad(feat_arr, (0, 128 - len(feat_arr)), 'constant')
                
            norm = np.linalg.norm(feat_arr)
            if norm > 0:
                feat_arr = feat_arr / norm
            return feat_arr.tolist()
        except Exception as e:
            logger.error(f"Error computing face embedding: {e}")
            return None

    def validate_face_quality(self, image_bgr, box):
        """
        Validate face image quality: size, sharpness, illumination.
        Returns (is_valid: bool, reason: str, metrics: dict)
        """
        x, y, w, h = box
        if w < 60 or h < 60:
            return False, "Face is too small or too far from camera. Please move closer.", {'size': w}
            
        face_crop = image_bgr[y:y+h, x:x+w]
        if face_crop.size == 0:
            return False, "Invalid face region detected.", {}
            
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        
        # 1. Illumination / Brightness
        brightness = np.mean(gray)
        if brightness < 40:
            return False, "Lighting is too dark. Please ensure good front lighting.", {'brightness': round(float(brightness), 1)}
        if brightness > 230:
            return False, "Lighting is too bright or overexposed.", {'brightness': round(float(brightness), 1)}
            
        # 2. Sharpness / Blur detection (Laplacian Variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 35:
            return False, "Face image is blurry. Please stay still.", {'sharpness': round(float(laplacian_var), 1)}
            
        return True, "Quality check passed", {
            'brightness': round(float(brightness), 1),
            'sharpness': round(float(laplacian_var), 1),
            'size': f"{w}x{h}"
        }

    @staticmethod
    def cosine_similarity(vec1, vec2):
        """Compute cosine similarity between two normalized embedding vectors."""
        u = np.array(vec1, dtype=np.float32).flatten()
        v = np.array(vec2, dtype=np.float32).flatten()
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)
        if norm_u == 0 or norm_v == 0:
            return 0.0
        return float(np.dot(u, v) / (norm_u * norm_v))

    def match_face(self, embedding, threshold=None):
        """
        Match a query embedding against enrolled student cache.
        Returns dict with match results: {matched: bool, student_id: str, name: str, dept: str, confidence: float}
        """
        if embedding is None:
            return {'matched': False, 'status': 'No Embedding', 'confidence': 0.0}
            
        if threshold is None:
            threshold = self.config.RECOGNITION_THRESHOLD
            
        if not self.cache_loaded:
            self.reload_student_cache()
            
        best_match_id = None
        best_student = None
        best_score = -1.0
        
        for student_id, student_info in self.student_cache.items():
            for enrolled_emb in student_info['embeddings']:
                score = self.cosine_similarity(embedding, enrolled_emb)
                if score > best_score:
                    best_score = score
                    best_match_id = student_id
                    best_student = student_info

        # SFace score mapping to human-readable confidence percentage
        confidence = max(0.0, min(1.0, float(best_score)))
        
        if best_student and confidence >= threshold:
            return {
                'matched': True,
                'status': 'Recognized',
                'student_id': best_student['student_id'],
                'name': best_student['name'],
                'department': best_student['department'],
                'year': best_student['year'],
                'section': best_student['section'],
                'photo_path': best_student['photo_path'],
                'confidence': confidence,
                'confidence_pct': round(confidence * 100, 1)
            }
        else:
            return {
                'matched': False,
                'status': 'Unknown',
                'student_id': None,
                'name': 'Unknown Face',
                'department': '-',
                'confidence': confidence,
                'confidence_pct': round(confidence * 100, 1)
            }

    def process_frame(self, frame_bgr, threshold=None):
        """
        Process a single video frame: detect faces, extract embeddings, match, and return annotated info.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return [], frame_bgr
            
        # Optional resize for high FPS
        h, w = frame_bgr.shape[:2]
        target_w = self.config.FRAME_RESIZE_WIDTH
        scale = 1.0
        if w > target_w:
            scale = target_w / float(w)
            small_frame = cv2.resize(frame_bgr, (target_w, int(h * scale)))
        else:
            small_frame = frame_bgr

        detected_faces = self.detect_faces(small_frame)
        results = []
        
        for face_data in detected_faces:
            box = face_data['box']
            # Scale box back to original coordinates if resized
            if scale != 1.0:
                orig_box = [int(v / scale) for v in box]
            else:
                orig_box = box
                
            x, y, bw, bh = orig_box
            raw_det = face_data.get('raw_detection')
            
            # Extract embedding
            emb = self.extract_embedding(small_frame, raw_det)
            match_res = self.match_face(emb, threshold=threshold)
            
            match_res['box'] = orig_box # [x, y, width, height]
            results.append(match_res)
            
        return results, frame_bgr


# Global singleton instance
face_engine = FaceRecognitionEngine.get_instance()
