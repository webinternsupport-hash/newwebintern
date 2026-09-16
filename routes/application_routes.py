import uuid
import os
import datetime
from flask import Blueprint, request, jsonify, g, send_file
from database import get_db_connection
from config import Config
from utils.auth import jwt_required
from utils.pdf_generator import generate_offer_letter_pdf
from utils.email_service import send_offer_letter_email_async
from utils.google_sheets import sync_event_to_google_sheets_async
from utils.logger import log_info, log_success, log_error

application_bp = Blueprint('application_bp', __name__)

@application_bp.route('/api/applications', methods=['POST'])
@jwt_required
def create_application():
    user_id = g.user_id
    user_email = (g.user_email or '').lower().strip()
    data = request.get_json() or {}
    
    internship_id = data.get('internship_id')
    if not internship_id:
        return jsonify({'error': 'internship_id is required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify user profile exists by id or email
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
    profile = cursor.fetchone()
    if not profile and user_email:
        cursor.execute("SELECT * FROM profiles WHERE LOWER(email) = ?", (user_email,))
        profile = cursor.fetchone()

    if not profile and (user_email or user_id):
        from utils.supabase_client import fetch_profile_from_supabase
        sp_prof = fetch_profile_from_supabase(user_email or user_id)
        if sp_prof:
            cursor.execute("""
                INSERT OR REPLACE INTO profiles (id, full_name, email, phone, college, department, degree, auth_provider, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'email', CURRENT_TIMESTAMP)
            """, (
                sp_prof.get('id') or user_id, sp_prof.get('full_name', 'Student'),
                sp_prof.get('email', user_email), sp_prof.get('phone'),
                sp_prof.get('college'), sp_prof.get('department'), sp_prof.get('degree')
            ))
            conn.commit()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (sp_prof.get('id') or user_id,))
            profile = cursor.fetchone()

    if not profile:
        conn.close()
        return jsonify({'error': 'Student profile not found'}), 404
        
    actual_user_id = profile['id']

    # Verify internship program exists
    cursor.execute("SELECT * FROM internships WHERE id = ?", (internship_id,))
    internship = cursor.fetchone()
    if not internship:
        conn.close()
        return jsonify({'error': 'Internship program not found'}), 404
        
    # Check for existing active application
    cursor.execute("""
        SELECT * FROM applications 
        WHERE (user_id = ? OR LOWER(user_id) = ?) AND internship_id = ? AND status != 'cancelled'
    """, (actual_user_id, profile['email'].lower(), internship_id))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        app_obj = dict(existing)
        return jsonify({
            'message': 'You are already enrolled in this internship program.',
            'application': app_obj,
            'is_existing': True
        }), 200

    app_id = str(uuid.uuid4())
    rand_code = uuid.uuid4().hex[:6].upper()
    offer_doc_num = f"WI-OFFER-2026-{rand_code}"
    cert_doc_num = f"WI-CERT-2026-{rand_code}"
    
    today = datetime.date.today()
    end_date_val = today + datetime.timedelta(days=28)
    start_date_str = today.strftime("%B %d, %Y")
    end_date_str = end_date_val.strftime("%B %d, %Y")
    
    # 1. Insert Application
    cursor.execute("""
        INSERT INTO applications (
            id, user_id, internship_id, status, offer_letter_sent, start_date, end_date,
            offer_letter_id, certificate_id, completion_status, google_sync_status, applied_at
        ) VALUES (?, ?, ?, 'active', 1, ?, ?, ?, ?, 'pending', 'synced', CURRENT_TIMESTAMP)
    """, (app_id, actual_user_id, internship_id, start_date_str, end_date_str, offer_doc_num, cert_doc_num))
    
    # 2. Insert Certificate stub
    cert_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO certificates (id, application_id, certificate_url, is_verified_paid, issued_at)
        VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
    """, (cert_doc_num, app_id, f"/api/certificates/{cert_doc_num}/pdf"))
    
    # 3. Insert Master Internship record
    master_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO master_internships (
            id, student_full_name, student_email, student_mobile, college_name, degree, department,
            internship_position, internship_domain, internship_start_date, internship_end_date,
            project_title, mentor_name, offer_id, certificate_id, user_id, application_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, profile['full_name'], profile['email'], profile['phone'] or profile['mobile'] or '',
        profile['college'] or 'University Student', profile['degree'] or 'Bachelor Degree', profile['department'] or 'General Track',
        internship['title'], internship['slug'], start_date_str, end_date_str,
        internship['project_name'] or 'Enterprise Internship Capstone',
        internship['guide_name'] or 'Dr. A. K. Sharma (Technical Director)',
        offer_doc_num, cert_doc_num, actual_user_id, app_id
    ))
    
    # 4. Generate Offer Letter PDF
    pdf_path = generate_offer_letter_pdf(
        student_name=profile['full_name'],
        email=profile['email'],
        internship_title=internship['title'],
        start_date=start_date_str,
        end_date=end_date_str,
        doc_number=offer_doc_num,
        guide_name=internship['guide_name'] or 'Dr. A. K. Sharma (Technical Director)'
    )
    
    # 5. Insert Document Record
    doc_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO documents (
            id, application_id, student_id, document_type, document_number, file_path, status, email_status
        ) VALUES (?, ?, ?, 'OFFER_LETTER', ?, ?, 'ISSUED', 'SENT')
    """, (doc_id, app_id, actual_user_id, offer_doc_num, pdf_path))

    conn.commit()
    
    # Sync application, certificate, master internship, document to Supabase PostgREST
    from utils.supabase_client import sync_application_to_supabase
    sync_application_to_supabase(
        app_data={
            'id': app_id, 'user_id': actual_user_id, 'internship_id': internship_id,
            'status': 'active', 'offer_letter_sent': True, 'start_date': start_date_str,
            'end_date': end_date_str, 'offer_letter_id': offer_doc_num,
            'certificate_id': cert_doc_num, 'completion_status': 'pending', 'google_sync_status': 'synced'
        },
        cert_data={
            'id': cert_doc_num, 'application_id': app_id,
            'certificate_url': f"/api/certificates/{cert_doc_num}/pdf", 'is_verified_paid': False
        },
        master_data={
            'id': master_id, 'student_full_name': profile['full_name'], 'student_email': profile['email'],
            'student_mobile': profile['phone'] or profile['mobile'] or '',
            'college_name': profile['college'] or 'University Student',
            'degree': profile['degree'] or 'Bachelor Degree', 'department': profile['department'] or 'General Track',
            'internship_position': internship['title'], 'internship_domain': internship['slug'],
            'internship_start_date': start_date_str, 'internship_end_date': end_date_str,
            'project_title': internship['project_name'] or 'Enterprise Internship Capstone',
            'mentor_name': internship['guide_name'] or 'Dr. A. K. Sharma (Technical Director)',
            'offer_id': offer_doc_num, 'certificate_id': cert_doc_num,
            'user_id': actual_user_id, 'application_id': app_id
        },
        doc_data={
            'id': doc_id, 'application_id': app_id, 'student_id': actual_user_id,
            'document_type': 'OFFER_LETTER', 'document_number': offer_doc_num,
            'file_path': pdf_path, 'status': 'ISSUED', 'email_status': 'SENT'
        }
    )

    # Fetch final application object
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.id = ?
    """, (app_id,))
    app_obj = dict(cursor.fetchone())
    conn.close()
    
    # Trigger background tasks
    send_offer_letter_email_async(profile['email'], profile['full_name'], internship['title'], pdf_path)
    sync_event_to_google_sheets_async('APPLICATION', {
        'application_id': app_id, 'offer_number': offer_doc_num, 'student': profile['full_name'], 'email': profile['email']
    })
    
    log_success(f"Enrolled {profile['email']} into {internship['title']}. App ID: {app_id}")
    
    return jsonify({
        'message': 'Application submitted and Offer Letter generated successfully!',
        'application': app_obj
    }), 201

@application_bp.route('/api/applications/me', methods=['GET'])
@jwt_required
def get_my_applications():
    user_id = g.user_id
    user_email = (g.user_email or '').lower().strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks, i.company_name, c.is_verified_paid
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        LEFT JOIN certificates c ON a.id = c.application_id OR a.certificate_id = c.id
        WHERE a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?)
        ORDER BY a.applied_at DESC
    """, (user_id, user_email, user_email))
    apps = [dict(r) for r in cursor.fetchall()]
    
    # Fallback to Supabase if 0 local apps found
    if not apps and user_email:
        from utils.supabase_client import fetch_applications_from_supabase
        sp_apps = fetch_applications_from_supabase(user_id, user_email)
        if sp_apps:
            for sa in sp_apps:
                app_id = sa.get('id')
                intern_id = sa.get('internship_id')
                if app_id and intern_id:
                    cursor.execute("""
                        INSERT OR IGNORE INTO applications (id, user_id, internship_id, status, offer_letter_sent, start_date, end_date, offer_letter_id, certificate_id, completion_status, google_sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app_id, user_id, intern_id, sa.get('status', 'active'),
                        sa.get('offer_letter_sent', 1), sa.get('start_date'), sa.get('end_date'),
                        sa.get('offer_letter_id'), sa.get('certificate_id'), sa.get('completion_status', 'pending'),
                        sa.get('google_sync_status', 'synced')
                    ))
            conn.commit()
            
            cursor.execute("""
                SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks, i.company_name, c.is_verified_paid
                FROM applications a
                JOIN internships i ON a.internship_id = i.id
                LEFT JOIN certificates c ON a.id = c.application_id OR a.certificate_id = c.id
                WHERE a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?)
                ORDER BY a.applied_at DESC
            """, (user_id, user_email, user_email))
            apps = [dict(r) for r in cursor.fetchall()]

    for app in apps:
        # Fetch submissions for this app
        cursor.execute("SELECT * FROM submissions WHERE application_id = ? ORDER BY week_number ASC", (app['id'],))
        submissions = [dict(s) for s in cursor.fetchall()]
        app['submissions'] = submissions
        
        # Calculate completed weeks (where status = 'graded' or 'approved')
        completed_weeks = len([s for s in submissions if s.get('status') in ('graded', 'approved')])
        duration = app.get('duration_weeks') or 4
        app['completed_weeks'] = completed_weeks
        app['progress_percentage'] = min(100, int((completed_weeks / duration) * 100))
        
        # Check if tenure / end_date has passed or all tasks completed
        is_ended = False
        if app.get('completion_status') == 'completed' or completed_weeks >= duration:
            is_ended = True
        elif app.get('end_date'):
            try:
                end_dt = datetime.datetime.strptime(app['end_date'], "%B %d, %Y").date()
                is_ended = (datetime.date.today() >= end_dt)
            except Exception:
                is_ended = True
        else:
            is_ended = True
            
        app['is_tenure_completed'] = is_ended
        app['can_download_certificate'] = bool(app.get('is_verified_paid')) and is_ended
        
    conn.close()
    return jsonify({'applications': apps}), 200

@application_bp.route('/api/applications/<app_id>/offer-letter.pdf', methods=['GET'])
def download_offer_letter(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ? OR offer_letter_id = ?", (app_id, app_id))
    app_record = cursor.fetchone()
    
    if not app_record:
        conn.close()
        return jsonify({'error': 'Application record not found'}), 404
        
    doc_number = app_record['offer_letter_id']
    pdf_filename = f"{doc_number}.pdf"
    file_path = os.path.join(Config.OFFER_LETTERS_DIR, pdf_filename)
    
    # Always fetch student & program details to ensure fresh generation with latest assets & QR code
    cursor.execute("SELECT full_name, email FROM profiles WHERE id = ?", (app_record['user_id'],))
    prof = cursor.fetchone()
    cursor.execute("SELECT title, guide_name FROM internships WHERE id = ?", (app_record['internship_id'],))
    intern = cursor.fetchone()
    conn.close()
    
    s_name = prof['full_name'] if prof else "Internship Candidate"
    s_email = prof['email'] if prof else "student@webintern.com"
    i_title = intern['title'] if intern else "Virtual Internship Program"
    g_name = intern['guide_name'] if intern else "Dr. A. K. Sharma (Technical Director)"
    
    file_path = generate_offer_letter_pdf(
        student_name=s_name, email=s_email, internship_title=i_title,
        start_date=app_record['start_date'], end_date=app_record['end_date'],
        doc_number=doc_number, guide_name=g_name
    )
        
    return send_file(file_path, mimetype='application/pdf', as_attachment=False, download_name=f"Offer_Letter_{doc_number}.pdf")
