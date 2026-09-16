import jwt
import bcrypt
import datetime
from functools import wraps
from flask import request, jsonify, g
from config import Config
from database import get_db_connection
from utils.logger import log_debug, log_error, log_info

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        log_error(f"Password check failed: {e}")
        return False

def generate_jwt_token(payload: dict) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    payload_to_encode = payload.copy()
    payload_to_encode['exp'] = expiration
    token = jwt.encode(payload_to_encode, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def extract_token_from_request():
    # 1. Bearer Header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    # 2. Cookie
    token_cookie = request.cookies.get('token')
    if token_cookie:
        return token_cookie
    return None

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication token missing', 'code': 'UNAUTHORIZED'}), 401
        
        data = decode_jwt_token(token)
        if not data:
            return jsonify({'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}), 401
        
        g.user_id = data.get('sub')
        g.user_email = data.get('email')
        g.is_admin = data.get('is_admin', False)
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication token missing', 'code': 'UNAUTHORIZED'}), 401
        
        data = decode_jwt_token(token)
        if not data or not data.get('is_admin'):
            return jsonify({'error': 'Admin privileges required', 'code': 'FORBIDDEN'}), 403
        
        g.user_id = data.get('sub')
        g.user_email = data.get('email')
        g.is_admin = True
        return f(*args, **kwargs)
    return decorated

def relink_user_data_by_email(user_id: str, email: str):
    """
    Links any orphaned applications, master records, or documents to the newly created/logged-in profile ID by matching normalized email.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        norm_email = email.lower().strip()
        
        # Link master internships
        cursor.execute(
            "UPDATE master_internships SET user_id = ? WHERE LOWER(student_email) = ? AND (user_id IS NULL OR user_id = '')",
            (user_id, norm_email)
        )
        
        # Link applications where master record email matches
        cursor.execute("""
            UPDATE applications 
            SET user_id = ? 
            WHERE id IN (
                SELECT application_id FROM master_internships WHERE LOWER(student_email) = ?
            ) AND (user_id IS NULL OR user_id = '')
        """, (user_id, norm_email))
        
        conn.commit()
        log_info(f"Relinked orphaned records for email: {norm_email}")
    except Exception as e:
        log_error(f"Error relinking user data: {e}")
        conn.rollback()
    finally:
        conn.close()
