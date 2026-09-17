import sys
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from database import get_db_connection, init_db
from utils.auth import generate_jwt_token

def test_referral_workflow():
    print("=== STARTING REFER & EARN FEATURE SYSTEM TEST ===")
    
    app = create_app()
    client = app.test_client()
    init_db()
    
    # 1. Register Student A (The Referrer)
    print("\n[STEP 1] Registering Referrer Student A...")
    referrer_email = f"referrer_{uuid.uuid4().hex[:6]}@example.com"
    resp_a = client.post('/api/auth/register', json={
        'full_name': 'Referrer Student A',
        'email': referrer_email,
        'password': 'Password#123',
        'terms_accepted': True
    })
    print(f"  Status: {resp_a.status_code}")
    assert resp_a.status_code == 201
    token_a = resp_a.get_json()['token']
    user_a_id = resp_a.get_json()['profile']['id']
    
    # Get Student A stats & referral code
    stats_a = client.get('/api/referrals/my-stats', headers={'Authorization': f'Bearer {token_a}'}).get_json()
    ref_code_a = stats_a['referral_code']
    print(f"  Referrer A Code: {ref_code_a}")
    print(f"  Referrer A Link: {stats_a['referral_link']}")
    assert ref_code_a.startswith("WIREF-")
    assert stats_a['total_registered'] == 0
    assert stats_a['total_enrolled'] == 0
    assert stats_a['is_eligible_for_reward'] == False
    
    # 2. Register Student B using Student A's referral code
    print("\n[STEP 2] Registering Student B with Referral Code...")
    referee_b_email = f"referee_b_{uuid.uuid4().hex[:6]}@example.com"
    resp_b = client.post('/api/auth/register', json={
        'full_name': 'Referee Student B',
        'email': referee_b_email,
        'password': 'Password#123',
        'referral_code': ref_code_a,
        'terms_accepted': True
    })
    assert resp_b.status_code == 201
    token_b = resp_b.get_json()['token']
    user_b_id = resp_b.get_json()['profile']['id']
    
    # Verify Referrer A stats: 1 registered, 0 enrolled (sharing/registering alone gives NO certificate benefits)
    stats_a2 = client.get('/api/referrals/my-stats', headers={'Authorization': f'Bearer {token_a}'}).get_json()
    print(f"  Referrer A Stats after Student B Register: Registered={stats_a2['total_registered']}, Enrolled={stats_a2['total_enrolled']}")
    assert stats_a2['total_registered'] == 1
    assert stats_a2['total_enrolled'] == 0
    assert stats_a2['is_eligible_for_reward'] == False
    print("  => REGISTERED ALONE GIVES NO REWARD! PASSED ✓")
    
    # 3. Student B Enrolls in an Internship Program
    print("\n[STEP 3] Student B Enrolls in Internship Program...")
    # Find an internship
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM internships LIMIT 1")
    intern_row = c.fetchone()
    if intern_row:
        intern_id = intern_row['id']
    else:
        intern_id = str(uuid.uuid4())
        c.execute("INSERT INTO internships (id, title, slug) VALUES (?, 'Full Stack Web', 'full-stack')", (intern_id,))
        conn.commit()
    conn.close()
    
    resp_app_b = client.post('/api/applications', json={'internship_id': intern_id}, headers={'Authorization': f'Bearer {token_b}'})
    print(f"  Student B Application Status: {resp_app_b.status_code}")
    assert resp_app_b.status_code in (200, 201)
    
    # Verify Referrer A stats: 1 registered, 1 ENROLLED!
    stats_a3 = client.get('/api/referrals/my-stats', headers={'Authorization': f'Bearer {token_a}'}).get_json()
    print(f"  Referrer A Stats after Student B Enrollment: Registered={stats_a3['total_registered']}, Enrolled={stats_a3['total_enrolled']}")
    assert stats_a3['total_registered'] == 1
    assert stats_a3['total_enrolled'] == 1
    assert stats_a3['is_eligible_for_reward'] == False  # Needs 3
    print("  => ENROLLED REFERRAL +1 CREDIT COUNTED! PASSED ✓")
    
    # 4. Register & Enroll Student C & Student D
    print("\n[STEP 4] Registering & Enrolling Student C and Student D...")
    for idx, name in [(3, 'Student C'), (4, 'Student D')]:
        email = f"referee_{idx}_{uuid.uuid4().hex[:6]}@example.com"
        rb = client.post('/api/auth/register', json={
            'full_name': name, 'email': email, 'password': 'Password#123', 'referral_code': ref_code_a, 'terms_accepted': True
        })
        tb = rb.get_json()['token']
        client.post('/api/applications', json={'internship_id': intern_id}, headers={'Authorization': f'Bearer {tb}'})
        
    stats_a4 = client.get('/api/referrals/my-stats', headers={'Authorization': f'Bearer {token_a}'}).get_json()
    print(f"  Referrer A Stats after 3 Enrollments: Registered={stats_a4['total_registered']}, Enrolled={stats_a4['total_enrolled']}")
    assert stats_a4['total_enrolled'] == 3
    assert stats_a4['is_eligible_for_reward'] == True
    print("  => REWARD ELIGIBILITY THRESHOLD REACHED! PASSED ✓")
    
    # 5. Referrer A Enrolls and Claims Free Certificate Reward
    print("\n[STEP 5] Referrer A Enrolls and Claims 100% Free Certificate Reward...")
    resp_app_a = client.post('/api/applications', json={'internship_id': intern_id}, headers={'Authorization': f'Bearer {token_a}'})
    app_a_data = resp_app_a.get_json()['application']
    cert_a_id = app_a_data['certificate_id']
    
    claim_resp = client.post('/api/referrals/claim-reward', json={'certificate_id': cert_a_id}, headers={'Authorization': f'Bearer {token_a}'})
    print(f"  Claim Status Code: {claim_resp.status_code}")
    print(f"  Claim Response: {claim_resp.get_json()}")
    assert claim_resp.status_code == 200
    assert claim_resp.get_json()['is_verified_paid'] == True
    print("  => FREE CERTIFICATE REWARD CLAIMED SUCCESSFULLY! PASSED ✓")
    
    print("\n==================================================")
    print("🎉 REFER & EARN FEATURE VERIFICATION COMPLETED!")
    print("==================================================")

if __name__ == '__main__':
    test_referral_workflow()
