/**
 * AI Face Recognition Attendance Management System - Main Core JS
 */

// Web Audio API Chime Synthesizer for Recognition Events
class AudioFeedback {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
    }
  }

  playSuccess() {
    try {
      this.init();
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      
      const now = this.ctx.currentTime;
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now); // D5
      osc1.frequency.exponentialRampToValueAtTime(880.00, now + 0.15); // A5

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(880.00, now);
      osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.25); // D6

      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.ctx.destination);

      osc1.start(now);
      osc2.start(now + 0.05);
      osc1.stop(now + 0.35);
      osc2.stop(now + 0.35);
    } catch (e) {
      console.warn("Audio chime playback:", e);
    }
  }

  playAlert() {
    try {
      this.init();
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.setValueAtTime(180, now + 0.1);

      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.25);
    } catch (e) {
      console.warn("Audio alert playback:", e);
    }
  }
}

window.soundFeedback = new AudioFeedback();

// Initialize user interaction trigger for AudioContext
document.addEventListener('click', () => {
  window.soundFeedback.init();
}, { once: true });

// Live Digital Clock
function initLiveClock() {
  const clockElem = document.getElementById('liveClockText');
  if (!clockElem) return;

  function update() {
    const now = new Date();
    clockElem.textContent = now.toLocaleTimeString('en-US', {
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  update();
  setInterval(update, 1000);
}

// Toast Notifications System
function showToast(message, type = 'info', title = '') {
  const toastContainer = document.getElementById('toast-container') || createToastContainer();
  
  const iconMap = {
    success: 'bi-check-circle-fill text-success',
    danger: 'bi-x-circle-fill text-danger',
    warning: 'bi-exclamation-triangle-fill text-warning',
    info: 'bi-info-circle-fill text-info'
  };

  const toast = document.createElement('div');
  toast.className = `toast-tech toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <i class="bi ${iconMap[type] || iconMap.info} toast-icon"></i>
      <div class="toast-text">
        ${title ? `<strong class="toast-title">${title}</strong>` : ''}
        <span>${message}</span>
      </div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toast-fade-out 0.3s forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'toast-container-tech';
  document.body.appendChild(container);
  return container;
}

// Global API Helper
async function apiFetch(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error || `HTTP error! status: ${response.status}`);
    }
    return data;
  } catch (error) {
    console.error('API Fetch Error:', error);
    throw error;
  }
}

// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', () => {
  initLiveClock();

  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.app-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }
});
