import uuid
import datetime
from flask import Blueprint, request, jsonify, g
from database import get_db_connection
from utils.auth import (
    hash_password, check_password, generate_jwt_token, 
    jwt_required, relink_user_data_by_email
)
from utils.google_sheets import sync_event_to_google_sheets_async
from utils.logger import log_debug, log_info, log_error, log_success

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', data.get('mobile', '')).strip()
    phone_country_code = data.get('phone_country_code', '+91')
    college = data.get('college', '').strip()
    department = data.get('department', '').strip()
    degree = data.get('degree', '').strip()
    terms_accepted = bool(data.get('terms_accepted', False))
    marketing_opt_in = bool(data.get('marketing_opt_in', False))
    
    if not full_name or not email or not password:
        return jsonify({'error': 'Full name, email, and password are required.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM profiles WHERE LOWER(email) = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 400
        
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    
    cursor.execute("""
        INSERT INTO profiles (
            id, full_name, email, phone, phone_country_code, college, department, degree,
            password_hash, auth_provider, mobile, terms_accepted, marketing_opt_in, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'email', ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, full_name, email, phone, phone_country_code, college, department, degree, pw_hash, phone, terms_accepted, marketing_opt_in))
    
    conn.commit()
    conn.close()
    
    # Relink orphaned data
    relink_user_data_by_email(user_id, email)
    
    # Sync to Google Sheets
    sync_event_to_google_sheets_async('REGISTER', {
        'user_id': user_id, 'full_name': full_name, 'email': email, 'college': college
    })

    # Sync to Supabase public.profiles
    from utils.supabase_client import sync_profile_to_supabase
    sync_profile_to_supabase({
        'id': user_id, 'full_name': full_name, 'email': email, 'phone': phone,
        'phone_country_code': phone_country_code, 'college': college,
        'department': department, 'degree': degree, 'mobile': phone,
        'terms_accepted': terms_accepted, 'marketing_opt_in': marketing_opt_in
    })
    
    token = generate_jwt_token({'sub': user_id, 'email': email, 'is_admin': False})
    
    profile = {
        'id': user_id,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'college': college,
        'department': department,
        'degree': degree
    }
    
    log_success(f"Registered new student account: {email}")
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'profile': profile
    }), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()
    
    if not user or not check_password(password, user['password_hash']):
        conn.close()
        log_debug(f"Failed login attempt for: {email}")
        return jsonify({'error': 'Invalid email or password.'}), 401
        
    user_id = user['id']
    
    # Fetch active enrollments by user_id OR email match
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.user_id = ? OR LOWER(a.user_id) = ?
        ORDER BY a.applied_at DESC
    """, (user_id, email))
    enrollments_rows = cursor.fetchall()
    
    enrollments = [dict(r) for r in enrollments_rows]
    conn.close()
    
    token = generate_jwt_token({'sub': user_id, 'email': user['email'], 'is_admin': False})
    
    profile = {
        'id': user['id'],
        'full_name': user['full_name'],
        'email': user['email'],
        'phone': user['phone'] or user['mobile'],
        'college': user['college'],
        'department': user['department'],
        'degree': user['degree']
    }
    
    # Sync to Google Sheets
    sync_event_to_google_sheets_async('LOGIN', {
        'user_id': user_id, 'email': email, 'timestamp': str(datetime.datetime.utcnow())
    })
    
    log_success(f"Successful login for user: {email}")
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'profile': profile,
        'enrollments': enrollments
    }), 200

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required
def get_me():
    user_id = g.user_id
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, full_name, email, phone, college, department, degree, created_at FROM profiles WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Profile not found'}), 44
        
    profile = dict(user)
    
    # Get enrollments
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.user_id = ?
        ORDER BY a.applied_at DESC
    """, (user_id,))
    enrollments = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'profile': profile,
        'enrollments': enrollments
    }), 200

@auth_bp.route('/api/auth/google-sync', methods=['POST'])

def google_sync():
    data = request.get_json() or {}
    google_sub = data.get('google_account_id', data.get('sub', ''))
    email = data.get('email', '').strip().lower()
    full_name = data.get('full_name', data.get('name', 'Google Student')).strip()
    
    if not email:
        return jsonify({'error': 'Google account email required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()
    
    if user:
        user_id = user['id']
        cursor.execute("UPDATE profiles SET google_account_id = ?, auth_provider = 'google' WHERE id = ?", (google_sub, user_id))
    else:
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO profiles (id, full_name, email, auth_provider, google_account_id, created_at)
            VALUES (?, ?, ?, 'google', ?, CURRENT_TIMESTAMP)
        """, (user_id, full_name, email, google_sub))
        
    conn.commit()
    conn.close()
    
    relink_user_data_by_email(user_id, email)
    
    token = generate_jwt_token({'sub': user_id, 'email': email, 'is_admin': False})
    
    return jsonify({
        'message': 'Google sync authentication successful',
        'token': token,
        'profile': {'id': user_id, 'full_name': full_name, 'email': email}
    }), 200

@auth_bp.route('/oauth2callback', methods=['GET', 'POST'])
def oauth2callback():
    return jsonify({'message': 'Google OAuth Callback operational'}), 200
