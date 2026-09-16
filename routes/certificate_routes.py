import os
from flask import Blueprint, request, jsonify, send_file
from database import get_db_connection
from utils.pdf_generator import generate_certificate_pdf
from config import Config
from utils.logger import log_info, log_error

certificate_bp = Blueprint('certificate_bp', __name__)

@certificate_bp.route('/api/certificates/verify/<cert_id>', methods=['GET'])
def verify_certificate(cert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, a.start_date, a.end_date, a.completion_status,
               p.full_name as student_name, p.email as student_email, p.college,
               i.title as internship_title, i.slug as internship_slug, i.guide_name
        FROM certificates c
        JOIN applications a ON c.application_id = a.id
        JOIN profiles p ON a.user_id = p.id
        JOIN internships i ON a.internship_id = i.id
        WHERE c.id = ? OR a.certificate_id = ?
    """, (cert_id, cert_id))
    
    row = cursor.fetchone()
    
    if not row:
        # Check master record fallback
        cursor.execute("SELECT * FROM master_internships WHERE certificate_id = ?", (cert_id,))
        master_row = cursor.fetchone()
        if master_row:
            conn.close()
            return jsonify({
                'is_valid': True,
                'certificate_id': cert_id,
                'student_name': master_row['student_full_name'],
                'college_name': master_row['college_name'],
                'internship_title': master_row['internship_position'],
                'start_date': master_row['internship_start_date'],
                'end_date': master_row['internship_end_date'],
                'guide_name': master_row['mentor_name'],
                'is_verified_paid': True,
                'verification_authority': 'Web Intern Academic Board & MSME ISO Standard',
                'status': 'VERIFIED CREDENTIAL'
            }), 200
        else:
            conn.close()
            return jsonify({'is_valid': False, 'error': 'Invalid Certificate ID'}), 404
            
    cert_data = dict(row)
    conn.close()
    
    # Check if end date passed or completed
    is_ended = False
    if cert_data.get('completion_status') == 'completed':
        is_ended = True
    elif cert_data.get('end_date'):
        try:
            end_dt = datetime.datetime.strptime(cert_data['end_date'], "%B %d, %Y").date()
            is_ended = (datetime.date.today() >= end_dt)
        except Exception:
            is_ended = True
    else:
        is_ended = True
        
    if not cert_data['is_verified_paid']:
        status_text = 'PENDING VERIFICATION FEE'
    elif not is_ended:
        status_text = f"VERIFIED FEE PAID (RELEASED ON END DATE: {cert_data['end_date']})"
    else:
        status_text = 'VERIFIED CREDENTIAL'

    return jsonify({
        'is_valid': True,
        'certificate_id': cert_data['id'],
        'student_name': cert_data['student_name'],
        'student_email': cert_data['student_email'],
        'college_name': cert_data['college'] or 'University Student',
        'internship_title': cert_data['internship_title'],
        'start_date': cert_data['start_date'],
        'end_date': cert_data['end_date'],
        'guide_name': cert_data['guide_name'],
        'is_verified_paid': bool(cert_data['is_verified_paid']),
        'is_tenure_completed': is_ended,
        'issued_at': cert_data['issued_at'],
        'verification_authority': 'Web Intern Academic Board & MSME ISO Standard',
        'status': status_text
    }), 200

@certificate_bp.route('/api/certificates/<cert_id>/pdf', methods=['GET'])
def download_certificate_pdf(cert_id):
    import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, a.start_date, a.end_date, a.completion_status,
               p.full_name as student_name,
               i.title as internship_title
        FROM certificates c
        JOIN applications a ON c.application_id = a.id
        JOIN profiles p ON a.user_id = p.id
        JOIN internships i ON a.internship_id = i.id
        WHERE c.id = ? OR a.certificate_id = ?
    """, (cert_id, cert_id))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Certificate record not found'}), 404
        
    c_info = dict(row)
    conn.close()

    # Tenure completion check: must be after end_date or completion_status == 'completed'
    is_ended = False
    if c_info.get('completion_status') == 'completed':
        is_ended = True
    elif c_info.get('end_date'):
        try:
            end_dt = datetime.datetime.strptime(c_info['end_date'], "%B %d, %Y").date()
            is_ended = (datetime.date.today() >= end_dt)
        except Exception:
            is_ended = True
    else:
        is_ended = True

    if not c_info.get('is_verified_paid'):
        return jsonify({
            'error': 'Certificate is locked. Please unlock your official verified certificate by paying ₹199 via Razorpay.',
            'code': 'FEE_NOT_PAID',
            'is_verified_paid': False
        }), 403

    if not is_ended:
        return jsonify({
            'error': f"Certificate will be available upon completion of your internship tenure on {c_info['end_date']}.",
            'code': 'TENURE_NOT_ENDED',
            'end_date': c_info['end_date'],
            'is_verified_paid': True
        }), 403

    pdf_path = generate_certificate_pdf(
        student_name=c_info['student_name'],
        internship_title=c_info['internship_title'],
        start_date=c_info['start_date'],
        end_date=c_info['end_date'],
        cert_id=cert_id,
        is_paid=True
    )

    
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=False, download_name=f"Certificate_{cert_id}.pdf")
