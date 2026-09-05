# 🤖 AI Face Recognition Attendance Management System

A state-of-the-art, production-style, real-time AI-powered Face Recognition Attendance Management System built with **Python Flask**, **OpenCV DNN (YuNet / SFace)**, **MySQL**, and a high-aesthetic **Dark Glassmorphism Web Dashboard**.

Designed for colleges, universities, and enterprise institutions to automate student/staff attendance tracking in real-time through standard computer and USB webcams.

---

## 🌟 Key Features

- 👤 **Real-Time Multi-Face Recognition**: Sub-millisecond facial detection and recognition matching using 128-dimensional deep feature embeddings.
- 🛡️ **Anti-Duplicate Attendance Engine**: Enforces single-attendance per student per session/date with configurable cooldown timers and real-time audio chime feedback.
- 📸 **Multi-Angle Biometric Enrollment**: Captures multiple facial angles (Frontal, Left, Right, Expression) with real-time blur and lighting quality assessment.
- 📊 **Dynamic Analytics Dashboard**: Visualizes live metrics (Total Students, Present, Absent, Attendance Rate %) with interactive **Chart.js** trends and department breakdowns.
- 📁 **Data Export & Reporting**: One-click download of attendance logs in **CSV** and **Excel (.xlsx)** formats, plus a printable official ledger report.
- 🔒 **Biometric Privacy & GDPR Compliance**: Ephemeral video processing in RAM (no video storage), password hashing, session authentication, and student biometric purge capability.
- 🗄️ **Dual Database Engine**: Native **MySQL** database support with automatic fallback to **SQLite** for instant zero-configuration testing.

---

## 🏗️ System Architecture

```
                                  [ Webcam Feed / Browser Camera ]
                                                 │
                                                 ▼
                                     [ Flask WebSocket / REST ]
                                                 │
                                                 ▼
                       ┌──────────────────────────────────────────────────┐
                       │           OpenCV Computer Vision Engine          │
                       │  1. Face Detection (YuNet / Haar Cascade)        │
                       │  2. Quality Check (Laplacian Blur & Brightness)  │
                       │  3. Feature Extraction (SFace 128D Embeddings)   │
                       └─────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                                  [ Vector Cosine Matcher ]
                                (In-Memory Cache >= Threshold)
                                                 │
                                                 ▼
                                  [ Attendance Business Logic ]
                              (Duplicate Check + Session Cooldown)
                                                 │
                                                 ▼
                               ┌─────────────────┴─────────────────┐
                               ▼                                   ▼
                   [ MySQL / SQLite Database ]       [ Live Kiosk HUD & Sound Alert ]
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Flask 3.0, Flask-SocketIO, SQLAlchemy ORM |
| **Computer Vision** | OpenCV (`cv2`), YuNet DNN Face Detector, SFace Deep Recognizer, NumPy |
| **Database** | MySQL 8.0+ / PyMySQL (with transparent SQLite local fallback) |
| **Data Processing** | Pandas, OpenPyXL, Pillow |
| **Frontend** | HTML5, CSS3 Custom Theme, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons |
| **Visualizations** | Chart.js 4.x |
| **Audio** | Web Audio API Real-Time Synthesizer (Chime & Alert Beeps) |

---

## 📂 Project Structure

```
attendance-system/
│
├── app.py                          # Flask application entry point & Socket.IO server
├── config.py                       # Application configuration & path definitions
├── requirements.txt                # Python package dependencies
├── .env.example                    # Sample environment variables template
├── .env                            # Active environment configuration
├── README.md                       # Comprehensive documentation & setup manual
│
├── database/
│   ├── db.py                       # SQLAlchemy database initialization & auto-fallback
│   ├── schema.sql                  # Production MySQL DDL script
│   └── ai_attendance.db            # Auto-generated SQLite local database (if used)
│
├── models/
│   ├── user.py                     # Admin credentials & password hashing
│   ├── student.py                  # Student schema & biometric embedding serializer
│   ├── attendance.py               # Attendance record & anti-duplicate constraints
│   ├── settings.py                 # Dynamic system parameters
│   ├── activity_log.py             # System audit trails
│   └── weights/                    # Pretrained OpenCV DNN models (auto-downloaded)
│
├── routes/
│   ├── auth_routes.py              # Login, logout & session protection
│   ├── dashboard_routes.py         # Dashboard analytics & live stats API
│   ├── student_routes.py           # Student CRUD, face validation & biometric purge
│   ├── live_routes.py              # Real-time kiosk streaming & frame processing
│   ├── attendance_routes.py        # Search, filter, pagination, CSV & Excel export
│   ├── reports_routes.py           # Charts, analytics trends & print report
│   └── settings_routes.py          # Threshold, camera index & DB health check
│
├── services/
│   ├── face_recognition.py         # AI detection, SFace 128D embeddings & cosine matcher
│   ├── attendance.py               # Duplicate prevention & statistics service
│   └── camera.py                   # Thread-safe webcam capture & HUD overlay drawing
│
├── static/
│   ├── css/style.css               # Dark/glassmorphic custom design system
│   ├── js/
│   │   ├── main.js                 # Clock, toast alerts, Web Audio synthesizer
│   │   ├── live_recognition.js     # Live kiosk stream loop & canvas HUD renderer
│   │   ├── face_registration.js    # Multi-angle photo capture & quality check
│   │   ├── dashboard.js            # Chart.js dashboard graphs
│   │   ├── attendance.js           # Filtering, pagination & export triggers
│   │   └── reports.js              # Analytic trend charts & tables
│   └── uploads/students/           # Stored primary face previews
│
└── templates/
    ├── base.html                   # Master layout with sidebar & header
    ├── login.html                  # Admin authentication portal
    ├── dashboard.html              # Analytics & metric overview
    ├── live_attendance.html        # Live Kiosk with webcam HUD & live ticker
    ├── students.html               # Student directory
    ├── register.html               # Multi-step face registration
    ├── student_profile.html        # Student ledger & biometric controls
    ├── attendance.html             # Attendance logs & manual mark modal
    ├── reports.html                # Visual analytics report generator
    ├── print_report.html           # Printable official attendance sheet
    ├── settings.html               # System configuration & DB health
    ├── 404.html                    # Error pages
    └── 500.html
```

---

## 🚀 Quick Start & Installation

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd "c:\Users\jaiki\AI face recognition attendance management system"
```

### Step 2: Create and Activate Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Database Settings
By default, the application runs with `.env` settings.

#### Option A: Using MySQL (Recommended for Production)
1. Open MySQL (e.g. XAMPP, WampServer, or MySQL Workbench).
2. Create the database:
   ```sql
   CREATE DATABASE ai_attendance_system;
   ```
3. Update `.env` with your MySQL credentials:
   ```env
   USE_MYSQL=True
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=ai_attendance_system
   ```

#### Option B: Using SQLite (Zero Setup Required)
If MySQL is not installed or running, the system **automatically falls back to SQLite** (`database/ai_attendance.db`) with zero setup needed!

---

### Step 5: (Optional) Seed Demonstration Data
To populate the system with 8 demo students and past 7-day attendance trends for presentation:
```powershell
flask seed-demo-data
```

---

### Step 6: Start the Application Server
```powershell
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

- **Default Username:** `admin`
- **Default Password:** `admin123`

---

## 📷 How to Use the System

### 1. Registering a Student
1. Click **"Register Student"** in the sidebar.
2. Enter the student details (Student ID, Name, Department, Year, Section, Email).
3. Click **"Start Webcam for Face Enrollment"**.
4. Follow the on-screen pose prompts (Frontal, Left, Right, Smile).
5. Ensure the quality meter shows green ("Quality Excellent").
6. Capture 4 face samples and click **"Register Student & Biometrics"**.

### 2. Running the Live Attendance Kiosk
1. Navigate to **"Live Attendance"** in the sidebar.
2. Click **"Start Live Camera"**.
3. When a registered student steps in front of the camera:
   - Green bounding boxes and corner brackets highlight their face.
   - Their name, student ID, and confidence percentage appear.
   - An audio chime rings and their attendance is automatically recorded.
   - If they look at the camera again, the anti-duplication engine prevents duplicate database entries.

### 3. Managing Attendance Records & Exports
1. Navigate to **"Attendance Records"**.
2. Filter by Date, Department, or search for a specific Student ID.
3. Click **"Export CSV"** to download a spreadsheet, or **"Export Excel"** for a `.xlsx` report.
4. Click **"Print Report"** to generate an official institutional attendance sheet.

### 4. Viewing Analytics & Trends
1. Navigate to **"Analytics & Reports"**.
2. Select time intervals (Past 7 Days, 30 Days, Current Month).
3. View the Present vs. Absent trend lines and department comparison charts.

---

## 📱 Mobile Application (PWA & Native Android APK)

VisionAttenda AI can be used directly as a full-featured **Mobile Application** on smartphones and tablets:

### 1. Instant PWA Installation (Android & iOS)

No app store required! The system includes full Progressive Web App (PWA) capabilities with offline caching, mobile bottom navigation, and full-screen camera scanning:

#### On Android (Chrome / Edge):
1. Open Chrome on your Android smartphone or tablet.
2. Navigate to your server URL (e.g. `http://<your-ip>:5000` or `https://your-domain.com`).
3. Tap the **"Install VisionAttenda"** banner at the bottom or open the 3-dots menu and tap **"Install App"** / **"Add to Home screen"**.
4. The app icon will appear on your phone's home screen and launch in standalone full-screen native mode!

#### On iOS (iPhone / iPad - Safari):
1. Open Safari and navigate to your server URL.
2. Tap the **Share** button (box with an arrow up).
3. Scroll down and select **"Add to Home Screen"**.
4. Tap **Add**. VisionAttenda will launch like a native iOS application.

---

### 2. Native Mobile Features

- 🔄 **Front / Rear Camera Flip**: Proctors and teachers can switch between Selfie and Rear camera with a single tap.
- 📳 **Haptic Vibration Feedback**: The smartphone vibrates (`navigator.vibrate`) when attendance is successfully marked.
- 📱 **Mobile Bottom Navigation Bar**: Easy thumb-reach access to Dashboard, Students, Scanner, and Records.
- ⚡ **Offline App Shell Caching**: Instant load times on 4G/5G mobile networks via Service Worker.

---

### 3. Compiling a Native Android `.apk` (Capacitor)

To compile a standalone Android Studio project and installable `.apk`:

```powershell
# 1. Install Capacitor CLI
npm install @capacitor/core @capacitor/cli @capacitor/android

# 2. Initialize and add Android platform
npx cap add android

# 3. Open in Android Studio to build APK
npx cap open android
```
*(In Android Studio, click **Build > Build Bundle(s) / APK(s) > Build APK(s)** to generate your release or debug `.apk`)*

---

## 🔒 Security & Privacy Notice

- **Ephemeral Video Processing**: Video streams are analyzed in volatile memory (RAM) and are immediately discarded.
- **Biometric Minimization**: Only 128-dimensional floating-point mathematical vectors are stored for verification.
- **Biometric Purge Feature**: Administrators can permanently delete a student's facial embeddings anytime from the **Student Profile** page in compliance with institutional and GDPR data privacy standards.

---

## 🔧 Troubleshooting Guide

| Issue | Cause | Solution |
|---|---|---|
| **Camera not starting in browser** | Browser permissions blocked | Click the lock/camera icon in your browser address bar and grant Camera permission to `localhost`. |
| **"Could not connect to MySQL"** | MySQL service not running | Ensure MySQL is running via XAMPP / MySQL Workbench, or leave it to auto-fallback to SQLite. |
| **Low Recognition Accuracy** | Sub-optimal lighting or blur | Increase front lighting, face the camera directly, or adjust the Threshold slider in **Settings** to 60-65%. |
| **Port 5000 already in use** | Another service using port | Change `PORT=5001` in `.env` and restart `python app.py`. |

---

&copy; 2026 **VisionAttenda AI** &bull; Institutional Biometric Attendance Management Framework
"# AI-FACE-SMART-SYSTEM" 
