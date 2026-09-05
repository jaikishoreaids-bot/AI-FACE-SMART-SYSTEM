/**
 * AI Face Recognition Attendance Management System - Real-Time Kiosk Engine
 */

class LiveAttendanceKiosk {
  constructor() {
    this.video = document.getElementById('webcamVideo');
    this.canvas = document.getElementById('overlayCanvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    
    this.startBtn = document.getElementById('startCamBtn');
    this.stopBtn = document.getElementById('stopCamBtn');
    this.audioToggle = document.getElementById('audioToggle');
    this.thresholdSlider = document.getElementById('kioskThreshold');
    this.thresholdValueSpan = document.getElementById('thresholdDisplay');
    
    // Side card elements
    this.studentPhoto = document.getElementById('recognizedPhoto');
    this.studentName = document.getElementById('recognizedName');
    this.studentId = document.getElementById('recognizedId');
    this.studentDept = document.getElementById('recognizedDept');
    this.studentStatusBadge = document.getElementById('recognizedStatus');
    this.confidenceBar = document.getElementById('confidenceBar');
    this.confidenceText = document.getElementById('confidenceText');
    this.lastMarkedNotice = document.getElementById('lastMarkedNotice');
    
    // Bottom Counters
    this.presentCounter = document.getElementById('kioskPresentCount');
    this.absentCounter = document.getElementById('kioskAbsentCount');
    this.rateCounter = document.getElementById('kioskRateCount');
    this.activityFeed = document.getElementById('kioskActivityFeed');
    
    this.switchCamBtn = document.getElementById('switchCameraBtn');
    this.facingMode = 'user'; // 'user' (front) or 'environment' (back)
    
    this.stream = null;
    this.isProcessing = false;
    this.processInterval = null;
    this.audioEnabled = true;
    this.currentThreshold = parseFloat(this.thresholdSlider ? this.thresholdSlider.value : 0.65);
    
    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCtx = this.offscreenCanvas.getContext('2d');
    
    this.lastRecognizedId = null;
    this.lastRecognizedTimestamp = 0;
    
    this.initEvents();
  }

  initEvents() {
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => this.startCamera());
    }
    if (this.stopBtn) {
      this.stopBtn.addEventListener('click', () => this.stopCamera());
    }
    if (this.switchCamBtn) {
      this.switchCamBtn.addEventListener('click', () => this.toggleCameraFacing());
    }
    if (this.audioToggle) {
      this.audioToggle.addEventListener('change', (e) => {
        this.audioEnabled = e.target.checked;
      });
    }
    if (this.thresholdSlider) {
      this.thresholdSlider.addEventListener('input', (e) => {
        this.currentThreshold = parseFloat(e.target.value);
        if (this.thresholdValueSpan) {
          this.thresholdValueSpan.textContent = Math.round(this.currentThreshold * 100) + '%';
        }
      });
    }
  }

  async toggleCameraFacing() {
    this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
    showToast(`Switched to ${this.facingMode === 'user' ? 'Front' : 'Rear'} Camera`, 'info');
    if (this.stream) {
      this.stopCamera();
      await this.startCamera();
    }
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: this.facingMode
        },
        audio: false
      });

      this.video.srcObject = this.stream;
      await this.video.play();

      this.startBtn.classList.add('d-none');
      this.stopBtn.classList.remove('d-none');
      
      // Synchronize canvas dimensions with video
      this.video.addEventListener('loadedmetadata', () => {
        this.canvas.width = this.video.videoWidth || 640;
        this.canvas.height = this.video.videoHeight || 480;
        this.offscreenCanvas.width = 640;
        this.offscreenCanvas.height = 480;
      }, { once: true });

      // Start recognition frame processing loop (~6-8 FPS)
      this.processInterval = setInterval(() => this.captureAndProcessFrame(), 150);
      showToast(`Camera Started (${this.facingMode === 'user' ? 'Front' : 'Rear'})`, 'success', 'Scanner Active');
    } catch (err) {
      console.error('Camera access error:', err);
      showToast('Could not access webcam: ' + err.message, 'danger', 'Camera Error');
    }
  }

  stopCamera() {
    if (this.processInterval) {
      clearInterval(this.processInterval);
      this.processInterval = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.video) {
      this.video.srcObject = null;
    }
    if (this.ctx) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    this.startBtn.classList.remove('d-none');
    this.stopBtn.classList.add('d-none');
    showToast('Camera stopped.', 'info');
  }

  async captureAndProcessFrame() {
    if (!this.video || this.video.paused || this.video.ended || this.isProcessing) {
      return;
    }

    const vw = this.video.videoWidth || 640;
    const vh = this.video.videoHeight || 480;
    if (vw === 0 || vh === 0) return;

    this.isProcessing = true;

    // Draw current video frame to offscreen canvas
    this.offscreenCanvas.width = vw;
    this.offscreenCanvas.height = vh;
    this.offscreenCtx.drawImage(this.video, 0, 0, vw, vh);

    const frameDataUri = this.offscreenCanvas.toDataURL('image/jpeg', 0.85);

    try {
      const response = await fetch('/api/live/process_frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: frameDataUri,
          threshold: this.currentThreshold
        })
      });

      const data = await response.json();
      if (data.success) {
        this.renderOverlays(data.faces, vw, vh);
        this.handleRecognitionEvents(data);
      }
    } catch (err) {
      console.error('Frame processing network error:', err);
    } finally {
      this.isProcessing = false;
    }
  }

  renderOverlays(faces, vw, vh) {
    if (!this.ctx) return;

    this.canvas.width = vw;
    this.canvas.height = vh;
    this.ctx.clearRect(0, 0, vw, vh);

    if (!faces || faces.length === 0) {
      return;
    }

    for (const face of faces) {
      const [x, y, w, h] = face.box || [0, 0, 0, 0];
      const isMatched = face.matched;
      const primaryColor = isMatched ? '#10b981' : '#f59e0b';
      const labelText = isMatched 
        ? `${face.name} (${face.student_id}) - ${face.confidence_pct}%`
        : `Unknown Face (${face.confidence_pct}%)`;

      // 1. Draw Bounding Box
      this.ctx.strokeStyle = primaryColor;
      this.ctx.lineWidth = 2.5;
      this.ctx.strokeRect(x, y, w, h);

      // 2. Cyber Corner Accents
      const clen = Math.min(22, w * 0.25, h * 0.25);
      this.ctx.strokeStyle = isMatched ? '#34d399' : '#fbbf24';
      this.ctx.lineWidth = 4;

      // Top-Left
      this.ctx.beginPath();
      this.ctx.moveTo(x, y + clen);
      this.ctx.lineTo(x, y);
      this.ctx.lineTo(x + clen, y);
      this.ctx.stroke();

      // Top-Right
      this.ctx.beginPath();
      this.ctx.moveTo(x + w - clen, y);
      this.ctx.lineTo(x + w, y);
      this.ctx.lineTo(x + w, y + clen);
      this.ctx.stroke();

      // Bottom-Left
      this.ctx.beginPath();
      this.ctx.moveTo(x, y + h - clen);
      this.ctx.lineTo(x, y + h);
      this.ctx.lineTo(x + clen, y + h);
      this.ctx.stroke();

      // Bottom-Right
      this.ctx.beginPath();
      this.ctx.moveTo(x + w - clen, y + h);
      this.ctx.lineTo(x + w, y + h);
      this.ctx.lineTo(x + w, y + h - clen);
      this.ctx.stroke();

      // 3. Label Badge Header
      this.ctx.font = '600 13px Inter, sans-serif';
      const textMetrics = this.ctx.measureText(labelText);
      const bgW = textMetrics.width + 16;
      const bgH = 26;
      const badgeY = Math.max(0, y - bgH - 6);

      this.ctx.fillStyle = '#0f172a';
      this.ctx.fillRect(x, badgeY, bgW, bgH);
      this.ctx.strokeStyle = primaryColor;
      this.ctx.lineWidth = 1;
      this.ctx.strokeRect(x, badgeY, bgW, bgH);

      this.ctx.fillStyle = '#ffffff';
      this.ctx.fillText(labelText, x + 8, badgeY + 18);
    }
  }

  handleRecognitionEvents(data) {
    const { faces, attendance_events, today_summary } = data;

    // Update bottom counters
    if (today_summary) {
      if (this.presentCounter) this.presentCounter.textContent = today_summary.present_count;
      if (this.absentCounter) this.absentCounter.textContent = today_summary.absent_count;
      if (this.rateCounter) this.rateCounter.textContent = today_summary.attendance_rate + '%';
      
      if (today_summary.recent_attendance && this.activityFeed) {
        this.updateActivityFeed(today_summary.recent_attendance);
      }
    }

    // Check if a recognized student was detected
    const recognizedFace = faces ? faces.find(f => f.matched) : null;

    if (recognizedFace) {
      // Update Side Card
      this.updateStudentSideCard(recognizedFace);

      // Check attendance events for sound chime and mobile haptic vibration
      if (attendance_events && attendance_events.length > 0) {
        for (const evt of attendance_events) {
          if (!evt.was_duplicate) {
            // Audio chime
            if (this.audioEnabled) {
              window.soundFeedback.playSuccess();
            }
            // Mobile Haptic Vibration
            if (navigator.vibrate) {
              try {
                navigator.vibrate([100, 50, 100]);
              } catch (e) {}
            }
            showToast(`Attendance marked for ${evt.name} (${evt.student_id})`, 'success', 'Attendance Recorded');
          }
        }
      }
    }
  }

  updateStudentSideCard(face) {
    if (this.studentName) this.studentName.textContent = face.name || 'Unknown';
    if (this.studentId) this.studentId.textContent = `ID: ${face.student_id || 'N/A'}`;
    if (this.studentDept) this.studentDept.textContent = `${face.department || '-'} (${face.year || ''})`;
    
    if (this.studentPhoto && face.photo_path) {
      this.studentPhoto.src = face.photo_path;
    }

    if (this.confidenceBar) {
      this.confidenceBar.style.width = `${face.confidence_pct}%`;
    }
    if (this.confidenceText) {
      this.confidenceText.textContent = `${face.confidence_pct}% Confidence`;
    }

    if (this.studentStatusBadge) {
      this.studentStatusBadge.className = 'badge-tech-present';
      this.studentStatusBadge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Recognized & Present';
    }

    if (this.lastMarkedNotice) {
      const nowTime = new Date().toLocaleTimeString();
      this.lastMarkedNotice.innerHTML = `<span class="text-success"><i class="bi bi-broadcast me-1"></i> Live: Verified at ${nowTime}</span>`;
    }
  }

  updateActivityFeed(records) {
    if (!this.activityFeed) return;
    
    if (records.length === 0) {
      this.activityFeed.innerHTML = `
        <div class="text-center text-muted py-4">
          <i class="bi bi-person-bounding-box fs-2 mb-2 d-block opacity-50"></i>
          No attendance records logged today yet.
        </div>`;
      return;
    }

    this.activityFeed.innerHTML = records.map(r => `
      <div class="activity-feed-item">
        <div class="d-flex align-items-center gap-3">
          <div class="user-avatar" style="width: 38px; height: 38px; font-size: 13px;">
            ${r.student_name.charAt(0)}
          </div>
          <div>
            <div class="fw-bold text-light">${r.student_name} <span class="text-muted fw-normal">(${r.student_id})</span></div>
            <div class="text-muted" style="font-size: 11px;">${r.department} &bull; ${r.session_name || 'Morning'}</div>
          </div>
        </div>
        <div class="text-end">
          <span class="badge-tech-${r.status === 'Present' ? 'present' : (r.status === 'Late' ? 'late' : 'absent')}">${r.status}</span>
          <div class="text-muted mt-1" style="font-size: 11px;"><i class="bi bi-clock me-1"></i>${r.attendance_time}</div>
        </div>
      </div>
    `).join('');
  }
}

// Instantiate Kiosk when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('webcamVideo')) {
    window.kiosk = new LiveAttendanceKiosk();
  }
});
