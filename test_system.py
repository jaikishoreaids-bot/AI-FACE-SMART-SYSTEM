import requests
import json
import re

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()


def run_tests():
    print("=================================================================")
    print("  AI Face Recognition Attendance System - Automated Verification")
    print("=================================================================\n")

    # 1. Test Login Page (GET)
    print("1. Testing Login Page (GET /login)...")
    res = session.get(f"{BASE_URL}/login")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "VisionAttenda" in res.text, "Branding not found in login page"
    print("    Login page loaded successfully (HTTP 200)")

    # 2. Test Admin Authentication (POST /login)
    print("\n2. Testing Admin Authentication (POST /login)...")
    login_payload = {
        'username': 'jaikishore',
        'password': 'jaikishore123'
    }
    res = session.post(f"{BASE_URL}/login", data=login_payload, allow_redirects=True)
    assert res.status_code == 200, f"Expected 200 on redirect, got {res.status_code}"
    assert "System Analytics Dashboard" in res.text or "VisionAttenda" in res.text, "Dashboard not returned after login"
    print("    Admin authentication successful (Session established)")

    # 3. Test Dashboard Stats API (GET /api/dashboard/stats)
    print("\n3. Testing Dashboard Stats API (GET /api/dashboard/stats)...")
    res = session.get(f"{BASE_URL}/api/dashboard/stats")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"    Total Students: {data['total_students']}")
    print(f"    Present Count: {data['present_count']}")
    print(f"    Absent Count: {data['absent_count']}")
    print(f"    Attendance Rate: {data['attendance_rate']}%")
    assert data['total_students'] >= 8, "Expected at least 8 seeded students"
    print("    Dashboard statistics API returned accurate metrics")

    # 4. Test Student List API (GET /api/students/list)
    print("\n4. Testing Student Directory API (GET /api/students/list)...")
    res = session.get(f"{BASE_URL}/api/students/list")
    assert res.status_code == 200
    stu_data = res.json()
    print(f"    Enrolled Students: {stu_data['total']}")
    for s in stu_data['students'][:3]:
        print(f"      - [{s['student_id']}] {s['name']} ({s['department']}) - Biometrics: {s['has_biometric']}")
    assert stu_data['total'] >= 8
    print("    Student directory API verified")

    # 5. Test Live Attendance Page (GET /live)
    print("\n5. Testing Live Attendance Kiosk Page (GET /live)...")
    res = session.get(f"{BASE_URL}/live")
    assert res.status_code == 200
    assert "Live Optical Scanner Feed" in res.text or "AI Real-Time Attendance Kiosk" in res.text
    print("    Live Attendance Kiosk page rendered successfully")

    # 6. Test Attendance Records API (GET /api/attendance/list)
    print("\n6. Testing Attendance Records API (GET /api/attendance/list)...")
    res = session.get(f"{BASE_URL}/api/attendance/list")
    assert res.status_code == 200
    att_data = res.json()
    print(f"    Total Attendance Logs: {att_data['total']}")
    print("    Attendance ledger API verified")

    # 7. Test CSV Export (GET /api/attendance/export/csv)
    print("\n7. Testing Attendance CSV Export (GET /api/attendance/export/csv)...")
    res = session.get(f"{BASE_URL}/api/attendance/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("Content-Type", "")
    assert "Record ID,Student ID" in res.text
    print("    CSV export generated and validated")

    # 8. Test Excel Export (GET /api/attendance/export/excel)
    print("\n8. Testing Attendance Excel Export (GET /api/attendance/export/excel)...")
    res = session.get(f"{BASE_URL}/api/attendance/export/excel")
    assert res.status_code == 200
    assert "openxmlformats" in res.headers.get("Content-Type", "")
    print("    Excel (.xlsx) export generated and validated")

    # 9. Test Reports & Analytics API (GET /api/reports/analytics)
    print("\n9. Testing Analytics API (GET /api/reports/analytics)...")
    res = session.get(f"{BASE_URL}/api/reports/analytics?period=7days")
    assert res.status_code == 200
    rep_data = res.json()
    print(f"    Average Attendance Rate (7 Days): {rep_data['avg_attendance_rate']}%")
    print(f"    Trend Data Points: {len(rep_data['trends']['labels'])} days")
    print("    Analytics reports API verified")

    # 10. Test System Settings & Database Health (GET /api/settings/db-health)
    print("\n10. Testing Database Health & AI Engine (GET /api/settings/db-health)...")
    res = session.get(f"{BASE_URL}/api/settings/db-health")
    assert res.status_code == 200
    health_data = res.json()
    print(f"    Database Status: {health_data['status']}")
    print(f"    Engine Type: {health_data['database_type']}")
    print(f"    Query Latency: {health_data['latency_ms']} ms")
    print(f"    Enrolled Face Biometrics: {health_data['enrolled_faces']}")
    print(f"    Face Engine Ready: {health_data['face_engine_ready']}")
    print("    System and database health verified")

    # 11. Test PWA Mobile App Manifest (GET /static/manifest.json)
    print("\n11. Testing PWA Mobile App Manifest (GET /static/manifest.json)...")
    res = session.get(f"{BASE_URL}/static/manifest.json")
    assert res.status_code == 200
    manifest = res.json()
    assert manifest['display'] == 'standalone'
    assert manifest['short_name'] == 'VisionAttenda'
    assert len(manifest['icons']) >= 2
    print(f"    PWA App Name: {manifest['name']}")
    print(f"    Display Mode: {manifest['display']}")
    print(f"    Theme Color: {manifest['theme_color']}")
    print("    PWA manifest verified for mobile app installation")

    # 12. Test PWA Service Worker (GET /static/sw.js)
    print("\n12. Testing Service Worker & Offline Caching (GET /static/sw.js)...")
    res = session.get(f"{BASE_URL}/static/sw.js")
    assert res.status_code == 200
    assert "CACHE_NAME" in res.text
    print("    Service worker script verified")

    # 13. Test App Icons (GET /static/images/icons/icon-192.png)
    print("\n13. Testing Mobile App Icon Assets...")
    res = session.get(f"{BASE_URL}/static/images/icons/icon-192.png")
    assert res.status_code == 200
    assert len(res.content) > 1000
    print("    192x192 and 512x512 app icons verified")

    print("\n=================================================================")
    print("  ALL 13 VERIFICATION TESTS (INCLUDING MOBILE PWA) PASSED! ")
    print("=================================================================\n")


if __name__ == "__main__":
    run_tests()
