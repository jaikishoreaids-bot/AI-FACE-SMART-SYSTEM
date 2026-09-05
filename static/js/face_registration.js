/**
 * AI Face Recognition Attendance Management System - Student Registration Engine
 */

class FaceRegistrationController {
  constructor() {
    this.video = document.getElementById('regWebcamVideo');
    this.canvas = document.getElementById('regCanvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    
    this.startCamBtn = document.getElementById('regStartCamBtn');
    this.captureBtn = document.getElementById('captureSampleBtn');
    this.samplesGallery = document.getElementById('capturedSamplesGallery');
    this.samplesProgressBar = document.getElementById('samplesProgressBar');
    this.samplesProgressText = document.getElementById('samplesProgressText');
    this.qualityStatus = document.getElementById('faceQualityStatus');
    this.submitBtn = document.getElementById('submitStudentBtn');
    this.form = document.getElementById('studentRegistrationForm');
    
    this.switchCamBtn = document.getElementById('regSwitchCameraBtn');
    this.facingMode = 'user'; // 'user' or 'environment'
    
    this.stream = null;
    this.capturedSamples = []; // Array of base64 data URIs
    this.requiredSamples = 4;
    this.qualityCheckInterval = null;
    this.isCheckingQuality = false;

    this.promptSteps = [
      "Look straight directly into the camera (Frontal View)",
      "Turn your head slightly to the left",
      "Turn your head slightly to the right",
      "Smile naturally or tilt slightly upwards"
    ];

    this.initEvents();
  }

  initEvents() {
    if (this.startCamBtn) {
      this.startCamBtn.addEventListener('click', () => this.startCamera());
    }
    if (this.switchCamBtn) {
      this.switchCamBtn.addEventListener('click', () => this.toggleCameraFacing());
    }
    if (this.captureBtn) {
      this.captureBtn.addEventListener('click', () => this.captureSample());
    }
    if (this.form) {
      this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }
  }

  async toggleCameraFacing() {
    this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
    showToast(`Switched to ${this.facingMode === 'user' ? 'Front' : 'Rear'} Camera`, 'info');
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      if (this.qualityCheckInterval) clearInterval(this.qualityCheckInterval);
      await this.startCamera();
    }
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: this.facingMode },
        audio: false
      });

      this.video.srcObject = this.stream;
      await this.video.play();

      this.startCamBtn.classList.add('d-none');
      this.captureBtn.disabled = false;
      
      this.updatePrompt();

      // Real-time quality checker loop
      this.qualityCheckInterval = setInterval(() => this.checkFrameQuality(), 400);
      showToast('Camera active. Follow the angle guidance to capture face samples.', 'info');
    } catch (err) {
      console.error('Camera access error:', err);
      showToast('Could not access camera: ' + err.message, 'danger');
    }
  }

  updatePrompt() {
    const promptElem = document.getElementById('captureAnglePrompt');
    if (!promptElem) return;
    const currentIdx = Math.min(this.capturedSamples.length, this.promptSteps.length - 1);
    promptElem.textContent = `Pose ${this.capturedSamples.length + 1} of ${this.requiredSamples}: ${this.promptSteps[currentIdx]}`;
  }

  async checkFrameQuality() {
    if (!this.video || this.video.paused || this.isCheckingQuality) return;

    const vw = this.video.videoWidth || 640;
    const vh = this.video.videoHeight || 480;
    if (vw === 0 || vh === 0) return;

    this.isCheckingQuality = true;

    this.canvas.width = vw;
    this.canvas.height = vh;
    this.ctx.drawImage(this.video, 0, 0, vw, vh);

    const frameDataUri = this.canvas.toDataURL('image/jpeg', 0.75);

    try {
      const response = await fetch('/api/students/validate-face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: frameDataUri })
      });

      const res = await response.json();
      if (this.qualityStatus) {
        if (res.valid) {
          this.qualityStatus.className = 'text-success fw-bold';
          this.qualityStatus.innerHTML = `<i class="bi bi-shield-check me-1"></i> Quality Excellent (${res.metrics.sharpness} Sharpness, ${res.metrics.brightness} Brightness)`;
          this.captureBtn.classList.add('btn-tech-success');
          this.captureBtn.classList.remove('btn-tech-secondary');
        } else {
          this.qualityStatus.className = 'text-warning fw-bold';
          this.qualityStatus.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> ${res.message}`;
          this.captureBtn.classList.remove('btn-tech-success');
          this.captureBtn.classList.add('btn-tech-secondary');
        }
      }
    } catch (e) {
      // ignore transient quality check errors
    } finally {
      this.isCheckingQuality = false;
    }
  }

  captureSample() {
    if (this.capturedSamples.length >= this.requiredSamples) {
      showToast('All required samples already captured.', 'info');
      return;
    }

    const vw = this.video.videoWidth || 640;
    const vh = this.video.videoHeight || 480;
    this.canvas.width = vw;
    this.canvas.height = vh;
    this.ctx.drawImage(this.video, 0, 0, vw, vh);

    const dataUri = this.canvas.toDataURL('image/jpeg', 0.90);
    this.capturedSamples.push(dataUri);

    window.soundFeedback.playSuccess();
    this.renderSamplesGallery();
    this.updateProgress();
    this.updatePrompt();

    if (this.capturedSamples.length >= this.requiredSamples) {
      this.captureBtn.disabled = true;
      this.submitBtn.disabled = false;
      showToast('All face biometric samples captured! You can now submit the student record.', 'success');
    }
  }

  renderSamplesGallery() {
    if (!this.samplesGallery) return;

    this.samplesGallery.innerHTML = this.capturedSamples.map((img, idx) => `
      <div class="col-3 position-relative mb-2">
        <div class="card bg-dark border-primary overflow-hidden shadow-sm" style="height: 90px;">
          <img src="${img}" class="w-100 h-100 object-fit-cover" alt="Sample ${idx + 1}">
          <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 p-1 m-1 lh-1" onclick="window.regController.removeSample(${idx})">
            &times;
          </button>
        </div>
        <div class="text-center text-muted" style="font-size: 11px;">Sample #${idx + 1}</div>
      </div>
    `).join('');
  }

  removeSample(idx) {
    this.capturedSamples.splice(idx, 1);
    this.renderSamplesGallery();
    this.updateProgress();
    this.updatePrompt();
    this.captureBtn.disabled = false;
    this.submitBtn.disabled = this.capturedSamples.length < this.requiredSamples;
  }

  updateProgress() {
    const pct = Math.round((this.capturedSamples.length / this.requiredSamples) * 100);
    if (this.samplesProgressBar) {
      this.samplesProgressBar.style.width = `${pct}%`;
    }
    if (this.samplesProgressText) {
      this.samplesProgressText.textContent = `${this.capturedSamples.length} / ${this.requiredSamples} Samples Captured`;
    }
  }

  async handleFormSubmit(e) {
    e.preventDefault();

    if (this.capturedSamples.length < 2) {
      showToast('Please capture at least 2 face samples before saving.', 'warning');
      return;
    }

    const payload = {
      student_id: document.getElementById('student_id').value.trim(),
      name: document.getElementById('name').value.trim(),
      department: document.getElementById('department').value.trim(),
      year: document.getElementById('year').value.trim(),
      section: document.getElementById('section').value.trim(),
      email: document.getElementById('email').value.trim(),
      phone: document.getElementById('phone').value.trim(),
      face_images: this.capturedSamples
    };

    this.submitBtn.disabled = true;
    this.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Generating AI Embeddings...';

    try {
      const res = await apiFetch('/api/students/register', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (res.success) {
        showToast(res.message, 'success', 'Student Enrolled');
        setTimeout(() => {
          window.location.href = `/student/${payload.student_id}`;
        }, 1200);
      }
    } catch (err) {
      showToast(err.message, 'danger', 'Registration Failed');
      this.submitBtn.disabled = false;
      this.submitBtn.innerHTML = '<i class="bi bi-person-check-fill me-2"></i> Register Student & Biometrics';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('regWebcamVideo')) {
    window.regController = new FaceRegistrationController();
  }
});
