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
    
    # Check if user already exists locally
    cursor.execute("SELECT id FROM profiles WHERE LOWER(email) = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 400
        
    # Create Supabase Auth user & sync to public.profiles first to get canonical user ID
    from utils.supabase_client import create_supabase_user, sync_profile_to_supabase
    sp_res = create_supabase_user(email, password, user_metadata={
        'full_name': full_name,
        'college': college,
        'department': department,
        'degree': degree,
        'phone': phone
    })
    
    if sp_res.get('success') and sp_res.get('user', {}).get('id'):
        user_id = str(sp_res['user']['id'])
    else:
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
    
    # Sync profile to Supabase public.profiles
    sync_profile_to_supabase({
        'id': user_id, 'full_name': full_name, 'email': email, 'phone': phone,
        'phone_country_code': phone_country_code, 'college': college,
        'department': department, 'degree': degree, 'mobile': phone,
        'terms_accepted': terms_accepted, 'marketing_opt_in': marketing_opt_in
    })

    # Sync to Google Sheets
    sync_event_to_google_sheets_async('REGISTER', {
        'user_id': user_id, 'full_name': full_name, 'email': email, 'college': college
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
    
    authenticated = False
    user_id = None
    profile_data = None
    
    if user and check_password(password, user['password_hash']):
        authenticated = True
        user_id = user['id']
        profile_data = dict(user)
    else:
        # Fallback to Supabase Auth login if local check failed or user was created in Supabase
        from utils.supabase_client import login_supabase_user, fetch_profile_from_supabase
        sp_login = login_supabase_user(email, password)
        if sp_login.get('success'):
            authenticated = True
            sp_user = sp_login.get('session', {}).get('user', {})
            user_id = sp_user.get('id') or (user['id'] if user else str(uuid.uuid4()))
            
            # Fetch profile from Supabase PostgREST or metadata
            sp_profile = fetch_profile_from_supabase(email) or {}
            meta = sp_user.get('user_metadata', {})
            
            full_name = sp_profile.get('full_name') or meta.get('full_name') or email.split('@')[0]
            phone = sp_profile.get('phone') or meta.get('phone') or ''
            college = sp_profile.get('college') or meta.get('college') or ''
            department = sp_profile.get('department') or meta.get('department') or ''
            degree = sp_profile.get('degree') or meta.get('degree') or ''
            pw_hash = hash_password(password)
            
            # Upsert into local SQLite profiles table
            if user:
                cursor.execute("""
                    UPDATE profiles SET password_hash = ?, full_name = ?, college = ?, department = ?, degree = ? WHERE id = ?
                """, (pw_hash, full_name, college, department, degree, user['id']))
                user_id = user['id']
            else:
                cursor.execute("""
                    INSERT INTO profiles (id, full_name, email, phone, college, department, degree, password_hash, auth_provider, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'email', CURRENT_TIMESTAMP)
                """, (user_id, full_name, email, phone, college, department, degree, pw_hash))
            
            conn.commit()
            
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
            profile_data = dict(cursor.fetchone())
    
    if not authenticated or not profile_data:
        conn.close()
        log_debug(f"Failed login attempt for: {email}")
        return jsonify({'error': 'Invalid email or password.'}), 401
        
    # Fetch active enrollments by user_id OR email match
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?)
        ORDER BY a.applied_at DESC
    """, (user_id, email, email))
    enrollments_rows = cursor.fetchall()
    
    enrollments = [dict(r) for r in enrollments_rows]
    conn.close()
    
    relink_user_data_by_email(user_id, email)
    
    token = generate_jwt_token({'sub': user_id, 'email': profile_data['email'], 'is_admin': False})
    
    profile = {
        'id': profile_data['id'],
        'full_name': profile_data['full_name'],
        'email': profile_data['email'],
        'phone': profile_data.get('phone') or profile_data.get('mobile', ''),
        'college': profile_data.get('college', ''),
        'department': profile_data.get('department', ''),
        'degree': profile_data.get('degree', '')
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
    user_email = (g.user_email or '').lower().strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, full_name, email, phone, college, department, degree, created_at FROM profiles WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user and user_email:
        cursor.execute("SELECT id, full_name, email, phone, college, department, degree, created_at FROM profiles WHERE LOWER(email) = ?", (user_email,))
        user = cursor.fetchone()

    if not user and (user_email or user_id):
        # Fallback recovery from Supabase
        from utils.supabase_client import fetch_profile_from_supabase
        sp_prof = fetch_profile_from_supabase(user_email or user_id)
        if sp_prof:
            rec_id = sp_prof.get('id') or user_id
            rec_email = sp_prof.get('email') or user_email
            rec_name = sp_prof.get('full_name') or rec_email.split('@')[0]
            
            cursor.execute("""
                INSERT OR REPLACE INTO profiles (id, full_name, email, phone, college, department, degree, auth_provider, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'email', CURRENT_TIMESTAMP)
            """, (
                rec_id, rec_name, rec_email, sp_prof.get('phone'),
                sp_prof.get('college'), sp_prof.get('department'), sp_prof.get('degree')
            ))
            conn.commit()
            
            cursor.execute("SELECT id, full_name, email, phone, college, department, degree, created_at FROM profiles WHERE id = ?", (rec_id,))
            user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Profile not found'}), 404
        
    profile = dict(user)
    actual_user_id = profile['id']
    actual_email = profile['email'].lower()
    
    # Get enrollments locally
    cursor.execute("""
        SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?)
        ORDER BY a.applied_at DESC
    """, (actual_user_id, actual_email, actual_email))
    enrollments = [dict(r) for r in cursor.fetchall()]
    
    # Fallback to Supabase for enrollments if 0 found locally
    if not enrollments:
        from utils.supabase_client import fetch_applications_from_supabase
        sp_apps = fetch_applications_from_supabase(actual_user_id, actual_email)
        if sp_apps:
            for sa in sp_apps:
                # Restore application into SQLite
                app_id = sa.get('id')
                intern_id = sa.get('internship_id')
                if app_id and intern_id:
                    cursor.execute("""
                        INSERT OR IGNORE INTO applications (id, user_id, internship_id, status, offer_letter_sent, start_date, end_date, offer_letter_id, certificate_id, completion_status, google_sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        app_id, actual_user_id, intern_id, sa.get('status', 'active'),
                        sa.get('offer_letter_sent', 1), sa.get('start_date'), sa.get('end_date'),
                        sa.get('offer_letter_id'), sa.get('certificate_id'), sa.get('completion_status', 'pending'),
                        sa.get('google_sync_status', 'synced')
                    ))
            conn.commit()
            
            cursor.execute("""
                SELECT a.*, i.title as internship_title, i.slug as internship_slug, i.internship_emoji, i.duration_weeks
                FROM applications a
                JOIN internships i ON a.internship_id = i.id
                WHERE a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?)
                ORDER BY a.applied_at DESC
            """, (actual_user_id, actual_email, actual_email))
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
