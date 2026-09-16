import os
import requests
from config import Config
from utils.logger import log_info, log_success, log_error

try:
    from supabase import create_client, Client
    SUPABASE_SDK_AVAILABLE = True
except ImportError:
    SUPABASE_SDK_AVAILABLE = False
    Client = None

_supabase_client = None
_supabase_admin_client = None

def get_supabase_client():
    """
    Returns initialized Supabase Client using the Anon Key.
    """
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_SDK_AVAILABLE:
            log_error("Supabase SDK is not installed. Install with `pip install supabase`")
            return None
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_ANON_KEY
        if not url or not key:
            log_error("Supabase URL or Anon Key missing in environment configuration")
            return None
        try:
            _supabase_client = create_client(url, key)
        except Exception as e:
            log_error(f"Failed to initialize Supabase anon client: {e}")
            return None
    return _supabase_client

def get_supabase_admin_client():
    """
    Returns initialized Supabase Client using the Service Role Key.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        if not SUPABASE_SDK_AVAILABLE:
            log_error("Supabase SDK is not installed. Install with `pip install supabase`")
            return None
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
        if not url or not key:
            log_error("Supabase URL or Service Role Key missing in environment configuration")
            return None
        try:
            _supabase_admin_client = create_client(url, key)
        except Exception as e:
            log_error(f"Failed to initialize Supabase admin client: {e}")
            return None
    return _supabase_admin_client

def check_supabase_connection():
    """
    Tests and returns details on Supabase connectivity.
    """
    url = Config.SUPABASE_URL
    anon_key = Config.SUPABASE_ANON_KEY
    service_key = Config.SUPABASE_SERVICE_ROLE_KEY

    result = {
        'connected': False,
        'url': url,
        'sdk_available': SUPABASE_SDK_AVAILABLE,
        'auth_status': 'unknown',
        'rest_status': 'unknown',
        'storage_status': 'unknown',
        'details': {}
    }

    if not url:
        result['details']['error'] = 'SUPABASE_URL is not configured in environment'
        log_error("Supabase check failed: SUPABASE_URL not configured.")
        return result

    # 1. Test Auth Service Health
    try:
        auth_resp = requests.get(f"{url}/auth/v1/health", headers={'apikey': anon_key}, timeout=5)
        if auth_resp.status_code == 200:
            result['auth_status'] = 'ok'
            result['details']['auth'] = auth_resp.json()
        else:
            result['auth_status'] = f"error_{auth_resp.status_code}"
    except Exception as e:
        result['auth_status'] = f"connection_failed: {str(e)}"

    # 2. Test REST Service API with Service Role Key or Anon Key
    try:
        headers = {'apikey': service_key or anon_key, 'Authorization': f"Bearer {service_key or anon_key}"}
        rest_resp = requests.get(f"{url}/rest/v1/", headers=headers, timeout=5)
        if rest_resp.status_code in (200, 204):
            result['rest_status'] = 'ok'
        else:
            result['rest_status'] = f"status_{rest_resp.status_code}"
    except Exception as e:
        result['rest_status'] = f"connection_failed: {str(e)}"

    # 3. Test Storage Service with Admin SDK or REST
    admin_client = get_supabase_admin_client()
    if admin_client:
        try:
            buckets = admin_client.storage.list_buckets()
            result['storage_status'] = 'ok'
            result['details']['buckets'] = len(buckets)
        except Exception as e:
            result['storage_status'] = f"error: {str(e)}"
    else:
        try:
            headers = {'apikey': service_key, 'Authorization': f"Bearer {service_key}"}
            st_resp = requests.get(f"{url}/storage/v1/bucket", headers=headers, timeout=5)
            if st_resp.status_code == 200:
                result['storage_status'] = 'ok'
                result['details']['buckets'] = len(st_resp.json())
            else:
                result['storage_status'] = f"status_{st_resp.status_code}"
        except Exception as e:
            result['storage_status'] = f"connection_failed: {str(e)}"

    # Connection overall status is considered connected if Auth and REST/Storage respond
    if result['auth_status'] == 'ok' or result['rest_status'] == 'ok' or result['storage_status'] == 'ok':
        result['connected'] = True
        log_success(f"Supabase connection verified for {url}")
    else:
        log_error(f"Supabase connection test failed for {url}")

    return result

def create_supabase_user(email, password, user_metadata=None):
    """
    Creates an auto-confirmed user account directly in Supabase Auth.
    """
    url = Config.SUPABASE_URL
    service_key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
    if not url or not service_key:
        return {'success': False, 'error': 'Supabase configuration missing'}

    admin_url = f"{url}/auth/v1/admin/users"
    headers = {
        'apikey': service_key,
        'Authorization': f"Bearer {service_key}",
        'Content-Type': 'application/json'
    }
    payload = {
        'email': email,
        'password': password,
        'email_confirm': True,
        'user_metadata': user_metadata or {}
    }

    try:
        resp = requests.post(admin_url, json=payload, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            data = resp.json()
            log_success(f"Created Supabase account: {email} (ID: {data.get('id')})")
            
            # Sync user profile into Supabase public.profiles table
            meta = user_metadata or {}
            profile_data = {
                'id': data.get('id'),
                'full_name': meta.get('full_name', email.split('@')[0]),
                'email': email,
                'college': meta.get('college'),
                'department': meta.get('department'),
                'degree': meta.get('degree'),
                'auth_provider': 'email'
            }
            sync_profile_to_supabase(profile_data)
            
            return {'success': True, 'user': data}
        else:
            log_error(f"Failed to create Supabase account ({resp.status_code}): {resp.text}")
            return {'success': False, 'error': resp.text, 'status_code': resp.status_code}
    except Exception as e:
        log_error(f"Exception during Supabase user creation: {e}")
        return {'success': False, 'error': str(e)}

def login_supabase_user(email, password):
    """
    Authenticates a user account with Supabase Auth and retrieves JWT session.
    """
    url = Config.SUPABASE_URL
    anon_key = Config.SUPABASE_ANON_KEY
    if not url or not anon_key:
        return {'success': False, 'error': 'Supabase configuration missing'}

    login_url = f"{url}/auth/v1/token?grant_type=password"
    headers = {
        'apikey': anon_key,
        'Content-Type': 'application/json'
    }
    payload = {'email': email, 'password': password}

    try:
        resp = requests.post(login_url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            log_success(f"Logged into Supabase account: {email}")
            return {'success': True, 'session': data}
        else:
            log_error(f"Supabase login failed ({resp.status_code}): {resp.text}")
            return {'success': False, 'error': resp.text, 'status_code': resp.status_code}
    except Exception as e:
        log_error(f"Exception during Supabase user login: {e}")
        return {'success': False, 'error': str(e)}

def sync_profile_to_supabase(profile_data):
    """
    Upserts a student profile record into Supabase public.profiles PostgREST table.
    """
    url = Config.SUPABASE_URL
    service_key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
    if not url or not service_key:
        return False

    headers = {
        'apikey': service_key,
        'Authorization': f"Bearer {service_key}",
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    payload = {
        'id': str(profile_data.get('id')),
        'full_name': profile_data.get('full_name', ''),
        'email': profile_data.get('email', ''),
        'phone': profile_data.get('phone'),
        'phone_country_code': profile_data.get('phone_country_code', '+91'),
        'college': profile_data.get('college'),
        'department': profile_data.get('department'),
        'degree': profile_data.get('degree'),
        'auth_provider': profile_data.get('auth_provider', 'email'),
        'mobile': profile_data.get('mobile'),
        'terms_accepted': bool(profile_data.get('terms_accepted', False)),
        'marketing_opt_in': bool(profile_data.get('marketing_opt_in', False)),
        'google_account_id': profile_data.get('google_account_id')
    }

    try:
        resp = requests.post(f"{url}/rest/v1/profiles", json=payload, headers=headers, timeout=10)
        if resp.status_code in (200, 201, 204):
            log_success(f"Synced profile {payload['email']} to Supabase public.profiles")
            return True
        else:
            log_error(f"Failed to sync profile {payload['email']} to Supabase: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        log_error(f"Exception syncing profile {profile_data.get('email')} to Supabase: {e}")
        return False

def sync_all_profiles_to_supabase():
    """
    Reads all student profiles from local SQLite database and syncs them to Supabase public.profiles.
    """
    from database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    count = 0
    for r in rows:
        if sync_profile_to_supabase(r):
            count += 1
    log_success(f"Synced {count}/{len(rows)} student profiles from SQLite to Supabase public.profiles")
    return count


