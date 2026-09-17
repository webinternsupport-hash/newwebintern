import os
import datetime
from flask import Blueprint, request, jsonify, send_file
from database import get_db_connection
from utils.pdf_generator import generate_certificate_pdf
from config import Config
from utils.logger import log_info, log_error

certificate_bp = Blueprint('certificate_bp', __name__)

@certificate_bp.route('/api/certificates/verify/<cert_id>', methods=['GET'])
def verify_certificate(cert_id):
    cert_id_clean = cert_id.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Query applications table (matches offer_letter_id, certificate_id, cert.id, or app.id)
    cursor.execute("""
        SELECT a.id as application_id, a.offer_letter_id, a.certificate_id, a.start_date, a.end_date, a.completion_status,
               p.full_name as student_name, p.email as student_email, p.college,
               i.title as internship_title, i.slug as internship_slug, i.guide_name,
               c.id as cert_table_id, c.is_verified_paid, c.issued_at
        FROM applications a
        LEFT JOIN certificates c ON (a.id = c.application_id OR a.certificate_id = c.id)
        LEFT JOIN profiles p ON a.user_id = p.id
        LEFT JOIN internships i ON a.internship_id = i.id
        WHERE c.id = ? OR a.certificate_id = ? OR a.offer_letter_id = ? OR a.id = ?
    """, (cert_id_clean, cert_id_clean, cert_id_clean, cert_id_clean))
    
    row = cursor.fetchone()
    cert_data = None
    
    if row:
        cert_data = dict(row)
    else:
        # 2. Check master_internships fallback locally
        cursor.execute("""
            SELECT * FROM master_internships 
            WHERE certificate_id = ? OR offer_id = ? OR id = ? OR application_id = ?
        """, (cert_id_clean, cert_id_clean, cert_id_clean, cert_id_clean))
        master_row = cursor.fetchone()
        if master_row:
            mr = dict(master_row)
            cert_data = {
                'application_id': mr.get('application_id') or mr.get('id'),
                'offer_letter_id': mr.get('offer_id'),
                'certificate_id': mr.get('certificate_id'),
                'start_date': mr.get('internship_start_date'),
                'end_date': mr.get('internship_end_date'),
                'completion_status': 'completed',
                'student_name': mr.get('student_full_name'),
                'student_email': mr.get('student_email'),
                'college': mr.get('college_name'),
                'internship_title': mr.get('internship_position'),
                'guide_name': mr.get('mentor_name', 'Dr. A. K. Sharma (Technical Director)'),
                'is_verified_paid': 1,
                'issued_at': mr.get('created_at')
            }
        else:
            # 3. Fallback to Supabase PostgREST
            try:
                import requests
                url = Config.SUPABASE_URL
                key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
                if url and key:
                    headers = {'apikey': key, 'Authorization': f"Bearer {key}"}
                    # Query applications or master_internships in Supabase
                    r = requests.get(
                        f"{url}/rest/v1/applications?or=(id.eq.{cert_id_clean},offer_letter_id.eq.{cert_id_clean},certificate_id.eq.{cert_id_clean})&select=*",
                        headers=headers, timeout=5
                    )
                    if r.status_code == 200 and r.json():
                        sp_app = r.json()[0]
                        # Fetch profile name
                        sp_name = 'Student'
                        sp_email = ''
                        sp_college = 'University Student'
                        p_res = requests.get(f"{url}/rest/v1/profiles?id=eq.{sp_app.get('user_id')}&select=*", headers=headers, timeout=5)
                        if p_res.status_code == 200 and p_res.json():
                            sp_name = p_res.json()[0].get('full_name', 'Student')
                            sp_email = p_res.json()[0].get('email', '')
                            sp_college = p_res.json()[0].get('college') or 'University Student'
                        
                        cert_data = {
                            'application_id': sp_app.get('id'),
                            'offer_letter_id': sp_app.get('offer_letter_id'),
                            'certificate_id': sp_app.get('certificate_id'),
                            'start_date': sp_app.get('start_date', '2026-01-01'),
                            'end_date': sp_app.get('end_date', '2026-02-01'),
                            'completion_status': sp_app.get('completion_status', 'pending'),
                            'student_name': sp_name,
                            'student_email': sp_email,
                            'college': sp_college,
                            'internship_title': 'Virtual Internship Program',
                            'guide_name': 'Dr. A. K. Sharma (Technical Director)',
                            'is_verified_paid': 1,
                            'issued_at': str(datetime.datetime.now())
                        }
                    else:
                        m_res = requests.get(
                            f"{url}/rest/v1/master_internships?or=(id.eq.{cert_id_clean},offer_id.eq.{cert_id_clean},certificate_id.eq.{cert_id_clean})&select=*",
                            headers=headers, timeout=5
                        )
                        if m_res.status_code == 200 and m_res.json():
                            sm = m_res.json()[0]
                            cert_data = {
                                'application_id': sm.get('application_id') or sm.get('id'),
                                'offer_letter_id': sm.get('offer_id'),
                                'certificate_id': sm.get('certificate_id'),
                                'start_date': sm.get('internship_start_date', '2026-01-01'),
                                'end_date': sm.get('internship_end_date', '2026-02-01'),
                                'completion_status': 'completed',
                                'student_name': sm.get('student_full_name', 'Student'),
                                'student_email': sm.get('student_email', ''),
                                'college': sm.get('college_name', 'University Student'),
                                'internship_title': sm.get('internship_position', 'Virtual Internship Program'),
                                'guide_name': sm.get('mentor_name', 'Dr. A. K. Sharma (Technical Director)'),
                                'is_verified_paid': 1,
                                'issued_at': str(datetime.datetime.now())
                            }
            except Exception as e:
                log_error(f"Error querying Supabase verification fallback: {e}")

    conn.close()
    
    if not cert_data:
        return jsonify({
            'is_valid': False,
            'error': f'No official certificate or offer letter found matching ID: {cert_id_clean}'
        }), 404

    # Determine document type (Offer Letter vs Certificate)
    is_offer_letter = (
        cert_id_clean.upper().startswith('WI-OFFER') or 
        cert_id_clean == cert_data.get('offer_letter_id')
    )
    
    doc_type = 'Offer Letter' if is_offer_letter else 'Completion Certificate'
    
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

    if is_offer_letter:
        status_text = 'VERIFIED OFFICIAL OFFER LETTER'
    elif not cert_data.get('is_verified_paid'):
        status_text = 'PENDING VERIFICATION FEE'
    elif not is_ended:
        status_text = f"VERIFIED FEE PAID (RELEASED ON END DATE: {cert_data['end_date']})"
    else:
        status_text = 'VERIFIED CERTIFICATE BY WEB INTERN'

    return jsonify({
        'is_valid': True,
        'certificate_id': cert_id_clean,
        'application_id': cert_data.get('application_id'),
        'offer_letter_id': cert_data.get('offer_letter_id'),
        'doc_certificate_id': cert_data.get('certificate_id'),
        'document_type': doc_type,
        'is_offer_letter': is_offer_letter,
        'student_name': cert_data.get('student_name') or 'Student',
        'student_email': cert_data.get('student_email') or '',
        'college_name': cert_data.get('college') or 'University Student',
        'internship_title': cert_data.get('internship_title') or 'Virtual Internship Program',
        'start_date': cert_data.get('start_date') or '',
        'end_date': cert_data.get('end_date') or '',
        'guide_name': cert_data.get('guide_name') or 'Dr. A. K. Sharma (Technical Director)',
        'is_verified_paid': bool(cert_data.get('is_verified_paid', True if is_offer_letter else False)),
        'is_tenure_completed': is_ended,
        'issued_at': cert_data.get('issued_at'),
        'verification_authority': 'Web Intern Academic Board & MSME ISO Standard',
        'status': status_text,
        'message': f'This {doc_type.lower()} has been officially verified by Web Intern Platform.'
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
        # Check master record fallback locally
        cursor.execute("SELECT * FROM master_internships WHERE certificate_id = ? OR offer_id = ?", (cert_id, cert_id))
        master_row = cursor.fetchone()
        if master_row:
            c_info = {
                'student_name': master_row['student_full_name'],
                'internship_title': master_row['internship_position'],
                'start_date': master_row['internship_start_date'],
                'end_date': master_row['internship_end_date'],
                'is_verified_paid': 1,
                'completion_status': 'completed'
            }
        else:
            # Fallback to Supabase PostgREST master_internships
            try:
                import requests
                url = Config.SUPABASE_URL
                key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
                headers = {'apikey': key, 'Authorization': f"Bearer {key}"}
                r = requests.get(f"{url}/rest/v1/master_internships?certificate_id=eq.{cert_id}&select=*", headers=headers, timeout=5)
                if r.status_code == 200 and r.json():
                    sm = r.json()[0]
                    c_info = {
                        'student_name': sm.get('student_full_name', 'Student'),
                        'internship_title': sm.get('internship_position', 'Virtual Internship Program'),
                        'start_date': sm.get('internship_start_date', '2026-01-01'),
                        'end_date': sm.get('internship_end_date', '2026-02-01'),
                        'is_verified_paid': 1,
                        'completion_status': 'completed'
                    }
                else:
                    c_info = None
            except Exception:
                c_info = None
    else:
        c_info = dict(row)

    conn.close()

    if not c_info:
        return jsonify({'error': 'Certificate record not found'}), 404

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

    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Certificate_{cert_id}.pdf"
    )
