import unittest
import os
import io
import json
from app import create_app
from database import init_db
from seed import seed_database

class WebInternTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        app = create_app()
        cls.client = app.test_client()

    def test_01_sectors_and_internships(self):
        res = self.client.get('/api/sectors')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('sectors', data)
        self.assertGreaterEqual(len(data['sectors']), 8)

        res_i = self.client.get('/api/internships')
        self.assertEqual(res_i.status_code, 200)
        data_i = json.loads(res_i.data)
        self.assertGreaterEqual(data_i['total'], 10)

    def test_02_auth_and_enrollment_flow(self):
        # 1. Register User
        email = f"teststudent_{os.urandom(4).hex()}@college.edu"
        reg_payload = {
            "full_name": "Test Student",
            "email": email,
            "password": "Password123!",
            "phone": "+919876543210",
            "college": "Test Tech University",
            "department": "Computer Science",
            "terms_accepted": True
        }
        res_reg = self.client.post('/api/auth/register', json=reg_payload)
        self.assertEqual(res_reg.status_code, 201)
        reg_data = json.loads(res_reg.data)
        token = reg_data['token']
        self.assertIsNotNone(token)

        headers = {'Authorization': f'Bearer {token}'}

        # 2. Get Me
        res_me = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(res_me.status_code, 200)

        # 3. Get Internship ID
        res_int = self.client.get('/api/internships')
        internships = json.loads(res_int.data)['internships']
        target_internship = internships[0]

        # 4. Enroll / Apply
        res_app = self.client.post('/api/applications', json={'internship_id': target_internship['id']}, headers=headers)
        self.assertEqual(res_app.status_code, 201)
        app_data = json.loads(res_app.data)['application']
        self.assertIsNotNone(app_data['offer_letter_id'])

        # 5. Fetch My Applications
        res_my_apps = self.client.get('/api/applications/me', headers=headers)
        self.assertEqual(res_my_apps.status_code, 200)
        my_apps = json.loads(res_my_apps.data)['applications']
        self.assertEqual(len(my_apps), 1)

        # 6. Stream Offer Letter PDF
        offer_id = app_data['offer_letter_id']
        res_pdf = self.client.get(f"/api/applications/{app_data['id']}/offer-letter.pdf")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.content_type, 'application/pdf')

        # 7. Upload Task Submission PDF
        pdf_bytes = b"%PDF-1.4 mock pdf content for testing week deliverable"
        data_upload = {
            'application_id': app_data['id'],
            'week_number': '1',
            'file': (io.BytesIO(pdf_bytes), 'week1_deliverable.pdf')
        }
        res_upload = self.client.post('/api/submissions/upload', data=data_upload, headers=headers, content_type='multipart/form-data')
        self.assertEqual(res_upload.status_code, 201)

        # 8. Admin Login & Grade Submission
        res_adm = self.client.post('/api/admin/login', json={'email': 'admin@webintern.com', 'password': 'admin123'})
        self.assertEqual(res_adm.status_code, 200)
        adm_token = json.loads(res_adm.data)['token']
        adm_headers = {'Authorization': f'Bearer {adm_token}'}

        res_subs = self.client.get('/api/admin/submissions', headers=adm_headers)
        sub_list = json.loads(res_subs.data)['submissions']
        self.assertGreaterEqual(len(sub_list), 1)
        sub_id = sub_list[0]['id']

        res_grade = self.client.post('/api/admin/grade-submission', json={
            'submission_id': sub_id, 'marks': 9.5, 'feedback': 'Excellent work!', 'status': 'graded'
        }, headers=adm_headers)
        self.assertEqual(res_grade.status_code, 200)

        # 9. Create Razorpay Payment Order & Unlock Certificate
        cert_id = app_data['certificate_id']
        res_order = self.client.post('/api/payments/create-order', json={'certificate_id': cert_id}, headers=headers)
        self.assertEqual(res_order.status_code, 201)
        order_data = json.loads(res_order.data)

        res_pay = self.client.post('/api/payments/verify', json={
            'razorpay_order_id': order_data['order_id'],
            'certificate_id': cert_id
        }, headers=headers)
        self.assertEqual(res_pay.status_code, 200)

        # 10. Public Certificate Verification
        res_verify = self.client.get(f'/api/certificates/verify/{cert_id}')
        self.assertEqual(res_verify.status_code, 200)
        v_data = json.loads(res_verify.data)
        self.assertTrue(v_data['is_valid'])
        self.assertTrue(v_data['is_verified_paid'])

        # 11. Stream Certificate PDF - check tenure gate
        res_cert_pdf_early = self.client.get(f'/api/certificates/{cert_id}/pdf')
        self.assertEqual(res_cert_pdf_early.status_code, 403)
        early_data = json.loads(res_cert_pdf_early.data)
        self.assertEqual(early_data['code'], 'TENURE_NOT_ENDED')

        # Mark application completion_status = 'completed' to simulate tenure end
        from database import get_db_connection
        conn = get_db_connection()
        conn.cursor().execute("UPDATE applications SET completion_status = 'completed' WHERE id = ?", (app_data['id'],))
        conn.commit()
        conn.close()

        res_cert_pdf = self.client.get(f'/api/certificates/{cert_id}/pdf')
        self.assertEqual(res_cert_pdf.status_code, 200)
        self.assertEqual(res_cert_pdf.content_type, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
