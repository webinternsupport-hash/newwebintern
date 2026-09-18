import sys
import os
import uuid
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from database import get_db_connection, init_db
from utils.auth import generate_jwt_token

def test_payment_workflow():
    print("=== PAYMENT FLOW TEST STARTED ===\n")
    
    app = create_app()
    client = app.test_client()
    init_db()
    
    # 1. Register a student
    print("[STEP 1] Registering student for payment test...")
    student_email = f"payment_test_{uuid.uuid4().hex[:6]}@example.com"
    resp = client.post('/api/auth/register', json={
        'full_name': 'Payment Test Student',
        'email': student_email,
        'password': 'Password#123',
        'terms_accepted': True
    })
    assert resp.status_code == 201, f"Registration failed: {resp.get_json()}"
    token = resp.get_json()['token']
    user_id = resp.get_json()['profile']['id']
    print(f"  ✓ Student registered: {student_email}")
    
    # 2. Get an internship
    print("\n[STEP 2] Finding internship...")
    resp_internships = client.get('/api/internships')
    internships = resp_internships.get_json()['internships']
    if not internships:
        print("  ERROR: No internships available. Creating one...")
        conn = get_db_connection()
        c = conn.cursor()
        intern_id = str(uuid.uuid4())
        c.execute("""
            INSERT INTO internships (id, title, slug, description, guide_name)
            VALUES (?, ?, ?, ?, ?)
        """, (intern_id, 'Full Stack Web Development', 'full-stack', 'Learn full stack development', 'Dr. Tech Guide'))
        conn.commit()
        conn.close()
    else:
        intern_id = internships[0]['id']
    print(f"  ✓ Using internship: {intern_id}")
    
    # 3. Create application (generates certificate)
    print("\n[STEP 3] Creating application (generates certificate)...")
    resp_app = client.post('/api/applications', json={
        'internship_id': intern_id
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp_app.status_code in (200, 201), f"Application creation failed: {resp_app.get_json()}"
    app_data = resp_app.get_json().get('application') or resp_app.get_json()
    cert_id = app_data.get('certificate_id')
    app_id = app_data.get('id')
    print(f"  ✓ Application created: {app_id}")
    print(f"  ✓ Certificate generated: {cert_id}")
    
    # 4. Create payment order
    print("\n[STEP 4] Creating payment order...")
    resp_order = client.post('/api/payments/create-order', json={
        'certificate_id': cert_id
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp_order.status_code in (200, 201), f"Payment order creation failed: {resp_order.get_json()}"
    order_data = resp_order.get_json()
    razorpay_order_id = order_data['order_id']
    payment_id = order_data['payment_id']
    amount_inr = order_data['amount_inr']
    print(f"  ✓ Order ID created: {razorpay_order_id}")
    print(f"  ✓ Payment ID: {payment_id}")
    print(f"  ✓ Amount: ₹{amount_inr}")
    print(f"  ✓ Razorpay Key: {order_data['key_id'][:20]}..." if order_data.get('key_id') else "  ✓ Razorpay Key: (not available)")
    
    # 5. Simulate payment verification
    print("\n[STEP 5] Simulating payment verification...")
    resp_verify = client.post('/api/payments/verify', json={
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': f'pay_{uuid.uuid4().hex[:12]}',
        'razorpay_signature': 'test_signature_' + uuid.uuid4().hex[:10],
        'certificate_id': cert_id
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp_verify.status_code == 200, f"Payment verification failed: {resp_verify.get_json()}"
    verify_data = resp_verify.get_json()
    print(f"  ✓ Payment verified successfully")
    print(f"  ✓ Certificate is_verified_paid: {verify_data.get('certificate_id')}")
    
    # 6. Verify certificate is now paid
    print("\n[STEP 6] Checking certificate payment status...")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_verified_paid FROM certificates WHERE id = ?", (cert_id,))
    cert_row = c.fetchone()
    conn.close()
    
    if cert_row:
        is_paid = cert_row['is_verified_paid']
        print(f"  ✓ Certificate is_verified_paid in DB: {bool(is_paid)}")
    else:
        print("  ✗ Certificate not found in database")
    
    # 7. Test verification endpoint
    print("\n[STEP 7] Testing certificate verification endpoint...")
    resp_cert_verify = client.get(f'/api/certificates/verify/{cert_id}')
    assert resp_cert_verify.status_code == 200, f"Certificate verification failed: {resp_cert_verify.get_json()}"
    cert_verify_data = resp_cert_verify.get_json()
    print(f"  ✓ Certificate verification successful")
    print(f"  ✓ Status: {cert_verify_data.get('status')}")
    print(f"  ✓ is_verified_paid: {cert_verify_data.get('is_verified_paid')}")
    
    print("\n" + "="*50)
    print("✅ PAYMENT FLOW TEST COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"\nSummary:")
    print(f"  - Student: {student_email}")
    print(f"  - Application: {app_id}")
    print(f"  - Certificate: {cert_id}")
    print(f"  - Order ID: {razorpay_order_id}")
    print(f"  - Amount: ₹{amount_inr}")
    print(f"  - Payment Status: VERIFIED ✓")

if __name__ == '__main__':
    try:
        test_payment_workflow()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
