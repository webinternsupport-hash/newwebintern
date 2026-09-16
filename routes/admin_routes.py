import datetime
from flask import Blueprint, request, jsonify, g
from database import get_db_connection
from utils.auth import check_password, generate_jwt_token, admin_required
from utils.logger import log_info, log_success, log_error

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Admin email and password required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admins WHERE LOWER(email) = ?", (email,))
    admin = cursor.fetchone()
    
    if not admin or not check_password(password, admin['password_hash']):
        conn.close()
        return jsonify({'error': 'Invalid admin credentials'}), 401
        
    token = generate_jwt_token({'sub': admin['id'], 'email': admin['email'], 'is_admin': True})
    
    conn.close()
    log_success(f"Admin logged in: {email}")
    return jsonify({
        'message': 'Admin login successful',
        'token': token,
        'admin': {
            'id': admin['id'],
            'email': admin['email'],
            'full_name': admin['full_name']
        }
    }), 200

@admin_bp.route('/api/admin/overview', methods=['GET'])
@admin_required
def get_overview():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM profiles")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE status = 'pending'")
    pending_submissions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM certificates WHERE is_verified_paid = 1")
    paid_certificates = cursor.fetchone()[0]
    
    conn.close()
    return jsonify({
        'total_students': total_students,
        'total_applications': total_applications,
        'pending_submissions': pending_submissions,
        'paid_certificates': paid_certificates
    }), 200

@admin_bp.route('/api/admin/submissions', methods=['GET'])
@admin_required
def list_pending_submissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, p.full_name as student_name, p.email as student_email, i.title as internship_title
        FROM submissions s
        JOIN applications a ON s.application_id = a.id
        JOIN profiles p ON a.user_id = p.id
        JOIN internships i ON a.internship_id = i.id
        ORDER BY s.submitted_at DESC
    """)
    submissions = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return jsonify({'submissions': submissions}), 200

@admin_bp.route('/api/admin/grade-submission', methods=['POST'])
@admin_required
def grade_submission():
    data = request.get_json() or {}
    submission_id = data.get('submission_id')
    marks = data.get('marks')
    feedback = data.get('feedback', '')
    status = data.get('status', 'graded')  # graded, approved, revise
    
    if not submission_id or marks is None:
        return jsonify({'error': 'submission_id and marks are required'}), 400
        
    try:
        marks_val = float(marks)
    except ValueError:
        return jsonify({'error': 'marks must be a numeric value'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE submissions 
        SET marks = ?, feedback = ?, status = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP, reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (marks_val, feedback, status, g.user_email, submission_id))
    
    # Check if this completion marks 4 completed tasks
    cursor.execute("SELECT application_id FROM submissions WHERE id = ?", (submission_id,))
    sub_row = cursor.fetchone()
    if sub_row:
        app_id = sub_row['application_id']
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE application_id = ? AND status IN ('graded', 'approved')", (app_id,))
        completed_count = cursor.fetchone()[0]
        if completed_count >= 4:
            cursor.execute("UPDATE applications SET completion_status = 'completed' WHERE id = ?", (app_id,))
            cursor.execute("""
                SELECT c.id as cert_id, c.is_verified_paid, p.email as student_email, p.full_name as student_name,
                       i.title as internship_title, a.start_date, a.end_date
                FROM certificates c
                JOIN applications a ON c.application_id = a.id
                JOIN profiles p ON a.user_id = p.id
                JOIN internships i ON a.internship_id = i.id
                WHERE a.id = ?
            """, (app_id,))
            c_info = cursor.fetchone()
            if c_info and c_info['is_verified_paid']:
                from utils.pdf_generator import generate_certificate_pdf
                from utils.email_service import send_certificate_email_async
                pdf_path = generate_certificate_pdf(
                    student_name=c_info['student_name'],
                    internship_title=c_info['internship_title'],
                    start_date=c_info['start_date'],
                    end_date=c_info['end_date'],
                    cert_id=c_info['cert_id'],
                    is_paid=True
                )
                send_certificate_email_async(c_info['student_email'], c_info['student_name'], c_info['internship_title'], c_info['cert_id'], pdf_path)
                log_success(f"Dispatched completion Certificate email to {c_info['student_email']}")
    
    conn.commit()
    conn.close()
    
    log_success(f"Graded submission {submission_id} with {marks_val}/10 marks. Status: {status}")
    return jsonify({
        'message': 'Submission graded successfully',
        'submission_id': submission_id,
        'marks': marks_val,
        'status': status
    }), 200


@admin_bp.route('/api/admin/applications', methods=['GET'])
@admin_required
def list_all_applications():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, p.full_name as student_name, p.email as student_email, p.college, i.title as internship_title
        FROM applications a
        JOIN profiles p ON a.user_id = p.id
        JOIN internships i ON a.internship_id = i.id
        ORDER BY a.applied_at DESC
    """)
    apps = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return jsonify({'applications': apps}), 200
