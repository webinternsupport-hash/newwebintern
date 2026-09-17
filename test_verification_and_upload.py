import sys
import os
import uuid
import datetime

# Ensure project root is in import path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from database import get_db_connection, init_db
from utils.auth import generate_jwt_token
from config import Config

def test_all():
    print("=== STARTING WEB INTERN PLATFORM SYSTEM VERIFICATION ===")
    
    # 1. Initialize app & DB
    app = create_app()
    client = app.test_client()
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 2. Setup Test Student Profile
    test_email = f"test_student_{uuid.uuid4().hex[:6]}@example.com"
    test_user_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO profiles (id, full_name, email, college, department, degree)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (test_user_id, "Rahul Sharma", test_email, "IIT Bombay", "Computer Science", "B.Tech"))
    
    # Ensure an internship exists
    cursor.execute("SELECT id FROM internships LIMIT 1")
    row = cursor.fetchone()
    if row:
        intern_id = row['id']
    else:
        intern_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO internships (id, title, slug, short_description)
            VALUES (?, 'Web Development Internship', 'web-development', '4-week program')
        """, (intern_id,))
        
    app_id = str(uuid.uuid4())
    offer_id = f"WI-OFFER-2026-{uuid.uuid4().hex[:6].upper()}"
    cert_id = f"WI-CERT-2026-{uuid.uuid4().hex[:6].upper()}"
    
    cursor.execute("""
        INSERT INTO applications (
            id, user_id, internship_id, status, offer_letter_sent, start_date, end_date,
            offer_letter_id, certificate_id, completion_status
        ) VALUES (?, ?, ?, 'active', 1, 'September 01, 2026', 'September 28, 2026', ?, ?, 'pending')
    """, (app_id, test_user_id, intern_id, offer_id, cert_id))
    
    cursor.execute("""
        INSERT INTO certificates (id, application_id, certificate_url, is_verified_paid)
        VALUES (?, ?, ?, 1)
    """, (cert_id, app_id, f"/api/certificates/{cert_id}/pdf"))
    
    conn.commit()
    conn.close()
    print(f"[+] Test data created. Student: {test_email} | App ID: {app_id} | Offer ID: {offer_id} | Cert ID: {cert_id}")
    
    # 3. Test QR Verification Endpoint for Offer Letter
    print("\n[TEST 1] Testing QR Code Verification for Offer Letter...")
    resp = client.get(f"/api/certificates/verify/{offer_id}")
    print(f"  Status Code: {resp.status_code}")
    data = resp.get_json()
    print(f"  Response: {data}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert data.get('is_valid') == True
    assert data.get('is_offer_letter') == True
    assert data.get('status') == 'VERIFIED OFFICIAL OFFER LETTER'
    assert data.get('student_name') == 'Rahul Sharma'
    assert data.get('college_name') == 'IIT Bombay'
    print("  => OFFER LETTER VERIFICATION PASSED! ✓")
    
    # 4. Test QR Verification Endpoint for Certificate
    print("\n[TEST 2] Testing QR Code Verification for Certificate...")
    resp2 = client.get(f"/api/certificates/verify/{cert_id}")
    print(f"  Status Code: {resp2.status_code}")
    data2 = resp2.get_json()
    print(f"  Response: {data2}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    assert data2.get('is_valid') == True
    assert data2.get('is_offer_letter') == False
    assert data2.get('student_name') == 'Rahul Sharma'
    assert 'VERIFIED' in data2.get('status', '')
    print("  => CERTIFICATE VERIFICATION PASSED! ✓")

    # 5. Test QR Verification for Image Screenshot ID: WI-OFFER-2026-F06ACD
    print("\n[TEST 3] Testing QR Code Verification for WI-OFFER-2026-F06ACD (from screenshot)...")
    # Insert screenshot ID temporarily into DB to verify matching
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO applications (
            id, user_id, internship_id, status, offer_letter_sent, start_date, end_date,
            offer_letter_id, certificate_id, completion_status
        ) VALUES ('app_f06acd', ?, ?, 'active', 1, 'September 01, 2026', 'September 28, 2026', 'WI-OFFER-2026-F06ACD', 'WI-CERT-2026-F06ACD', 'pending')
    """, (test_user_id, intern_id))
    conn.commit()
    conn.close()
    
    resp3 = client.get("/api/certificates/verify/WI-OFFER-2026-F06ACD")
    print(f"  Status Code: {resp3.status_code}")
    data3 = resp3.get_json()
    print(f"  Response: {data3}")
    assert resp3.status_code == 200
    assert data3.get('is_valid') == True
    assert data3.get('status') == 'VERIFIED OFFICIAL OFFER LETTER'
    print("  => SCREENSHOT ID VERIFICATION PASSED! ✓")

    # 6. Test Task PDF Upload Endpoint
    print("\n[TEST 4] Testing Student Task PDF Upload...")
    token = generate_jwt_token({'sub': test_user_id, 'email': test_email, 'is_admin': False})
    
    import io
    pdf_bytes = b"%PDF-1.4 Mock PDF deliverable task file content for Web Intern"
    
    data_payload = {
        'application_id': app_id,
        'week_number': '1',
        'file': (io.BytesIO(pdf_bytes), 'Week_1_Capstone_Task.pdf')
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    resp_up = client.post('/api/submissions/upload', data=data_payload, headers=headers, content_type='multipart/form-data')
    print(f"  Status Code: {resp_up.status_code}")
    data_up = resp_up.get_json()
    print(f"  Response: {data_up}")
    assert resp_up.status_code == 201, f"Expected 201, got {resp_up.status_code}"
    assert data_up.get('status') == 'pending'
    assert 'submission_id' in data_up
    print("  => TASK PDF UPLOAD PASSED! ✓")

    print("\n==================================================")
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    test_all()
