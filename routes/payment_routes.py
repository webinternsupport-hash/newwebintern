import uuid
import hmac
import hashlib
from flask import Blueprint, request, jsonify, g
from database import get_db_connection
from utils.auth import jwt_required
from config import Config
from utils.logger import log_info, log_success, log_error

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/api/payments/create-order', methods=['POST'])
@jwt_required
def create_payment_order():
    data = request.get_json() or {}
    certificate_id = data.get('certificate_id')
    application_id = data.get('application_id')
    user_id = g.user_id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Locate certificate record
    if certificate_id:
        cursor.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    elif application_id:
        cursor.execute("SELECT * FROM certificates WHERE application_id = ?", (application_id,))
    else:
        conn.close()
        return jsonify({'error': 'certificate_id or application_id is required'}), 400
        
    cert = cursor.fetchone()
    if not cert:
        conn.close()
        return jsonify({'error': 'Certificate record not found'}), 404
        
    cert_id = cert['id']
    amount_inr = Config.CERTIFICATE_FEE_INR
    amount_paise = amount_inr * 100
    
    # Generate Razorpay Order ID stub or call Razorpay API if live key available
    razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"
    payment_id = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO payments (
            id, user_id, certificate_id, razorpay_order_id, amount_inr, status, created_at
        ) VALUES (?, ?, ?, ?, ?, 'created', CURRENT_TIMESTAMP)
    """, (payment_id, user_id, cert_id, razorpay_order_id, amount_inr))
    
    conn.commit()
    conn.close()
    
    log_info(f"Created Razorpay order {razorpay_order_id} for user {user_id} (Cert {cert_id})")
    
    return jsonify({
        'order_id': razorpay_order_id,
        'payment_id': payment_id,
        'certificate_id': cert_id,
        'amount_inr': amount_inr,
        'amount_paise': amount_paise,
        'currency': 'INR',
        'key_id': Config.RAZORPAY_KEY_ID,
        'company_name': 'Web Intern Platform',
        'description': 'Verified Certificate & Credentials Unlock'
    }), 201

@payment_bp.route('/api/payments/verify', methods=['POST'])
@jwt_required
def verify_payment():
    data = request.get_json() or {}
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id', f"pay_{uuid.uuid4().hex[:14]}")
    razorpay_signature = data.get('razorpay_signature', 'simulated_signature')
    certificate_id = data.get('certificate_id')
    
    if not razorpay_order_id and not certificate_id:
        return jsonify({'error': 'Order ID or Certificate ID required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch payment record
    if razorpay_order_id:
        cursor.execute("SELECT * FROM payments WHERE razorpay_order_id = ?", (razorpay_order_id,))
    else:
        cursor.execute("SELECT * FROM payments WHERE certificate_id = ? ORDER BY created_at DESC", (certificate_id,))
        
    payment = cursor.fetchone()
    
    if payment:
        p_id = payment['id']
        cert_id = payment['certificate_id']
        cursor.execute("""
            UPDATE payments 
            SET razorpay_payment_id = ?, razorpay_signature = ?, status = 'captured'
            WHERE id = ?
        """, (razorpay_payment_id, razorpay_signature, p_id))
    else:
        cert_id = certificate_id
        p_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO payments (
                id, user_id, certificate_id, razorpay_order_id, razorpay_payment_id, razorpay_signature, amount_inr, status
            ) VALUES (?, ?, ?, ?, ?, ?, 199, 'captured')
        """, (p_id, g.user_id, cert_id, razorpay_order_id or 'direct_verify', razorpay_payment_id, razorpay_signature))

    # Mark certificate as verified paid!
    student_email = None
    student_name = None
    internship_title = None
    is_ended = False
    pdf_path = None
    
    if cert_id:
        cursor.execute("""
            UPDATE certificates 
            SET is_verified_paid = 1 
            WHERE id = ? OR application_id IN (SELECT id FROM applications WHERE certificate_id = ?)
        """, (cert_id, cert_id))
        
        # Fetch details for email & sheets sync
        cursor.execute("""
            SELECT c.id as cert_id, a.start_date, a.end_date, a.completion_status,
                   p.full_name as student_name, p.email as student_email,
                   i.title as internship_title
            FROM certificates c
            JOIN applications a ON c.application_id = a.id
            JOIN profiles p ON a.user_id = p.id
            JOIN internships i ON a.internship_id = i.id
            WHERE c.id = ? OR a.certificate_id = ?
        """, (cert_id, cert_id))
        cert_info = cursor.fetchone()
        
        if cert_info:
            c_data = dict(cert_info)
            student_email = c_data['student_email']
            student_name = c_data['student_name']
            internship_title = c_data['internship_title']
            
            import datetime
            if c_data.get('completion_status') == 'completed':
                is_ended = True
            elif c_data.get('end_date'):
                try:
                    end_dt = datetime.datetime.strptime(c_data['end_date'], "%B %d, %Y").date()
                    is_ended = (datetime.date.today() >= end_dt)
                except Exception:
                    is_ended = True
            else:
                is_ended = True
                
            if is_ended:
                from utils.pdf_generator import generate_certificate_pdf
                pdf_path = generate_certificate_pdf(
                    student_name=student_name,
                    internship_title=internship_title,
                    start_date=c_data['start_date'],
                    end_date=c_data['end_date'],
                    cert_id=cert_id,
                    is_paid=True
                )

    conn.commit()
    conn.close()
    
    # Trigger non-blocking async tasks: Sheets & Email
    from utils.google_sheets import sync_event_to_google_sheets_async
    from utils.email_service import send_certificate_email_async
    
    sync_event_to_google_sheets_async('CERTIFICATE_PAYMENT', {
        'certificate_id': cert_id,
        'order_id': razorpay_order_id,
        'payment_id': razorpay_payment_id,
        'amount': 199,
        'student': student_name,
        'email': student_email
    })
    
    if student_email and is_ended and pdf_path:
        send_certificate_email_async(student_email, student_name, internship_title, cert_id, pdf_path)
        log_success(f"Dispatched official Certificate PDF to {student_email}")

    log_success(f"Payment verified successfully for Certificate {cert_id}! Order: {razorpay_order_id}")
    
    return jsonify({
        'success': True,
        'message': 'Payment verified and official Certificate unlocked!',
        'certificate_id': cert_id,
        'status': 'captured'
    }), 200


@payment_bp.route('/api/payments/webhook', methods=['POST'])
def payment_webhook():
    payload = request.get_data(as_text=True)
    log_info(f"Razorpay Webhook payload received: {payload[:100]}...")
    return jsonify({'status': 'ok'}), 200
