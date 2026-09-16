import threading
import requests
from config import Config
from utils.logger import log_info, log_error, log_success

def send_to_google_sheets(event_type, payload):
    """
    Synchronous HTTP dispatcher for Google Apps Script Webhook.
    """
    url = Config.GOOGLE_SHEETS_WEBHOOK_URL
    if not url:
        log_info(f"[SHEETS MOCK] Event '{event_type}' handled locally. Google Sheets URL not configured.")
        return {'success': False, 'error': 'Webhook URL not configured'}

    body = {
        "event": event_type,
        "data": payload
    }

    try:
        res = requests.post(url, json=body, timeout=12, allow_redirects=True)
        if res.status_code in (200, 201):
            log_success(f"Synced '{event_type}' to Google Sheets Webhook.")
            return {'success': True, 'response': res.text, 'status_code': res.status_code}
        else:
            log_error(f"Google Sheets Webhook returned HTTP {res.status_code}: {res.text[:150]}")
            return {'success': False, 'status_code': res.status_code, 'error': res.text}
    except Exception as e:
        log_error(f"Google Sheets Webhook failed for '{event_type}': {e}")
        return {'success': False, 'error': str(e)}

def sync_event_to_google_sheets_async(event_type, payload):
    """
    Non-blocking async webhook dispatcher for Google Apps Script sync.
    """
    def _post():
        send_to_google_sheets(event_type, payload)

    thread = threading.Thread(target=_post)
    thread.daemon = True
    thread.start()

def sync_all_existing_data_to_google_sheets():
    """
    Reads existing student profiles, applications, certificates, and payments from SQLite
    and syncs them to Google Sheets Webhook.
    """
    from database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    synced_counts = {'profiles': 0, 'applications': 0, 'certificates': 0, 'payments': 0}

    # 1. Profiles
    cursor.execute("SELECT id, full_name, email, phone, college, department, degree, created_at FROM profiles")
    profiles = [dict(r) for r in cursor.fetchall()]
    for p in profiles:
        res = send_to_google_sheets('REGISTER', p)
        if res.get('success'):
            synced_counts['profiles'] += 1

    # 2. Applications
    cursor.execute("""
        SELECT a.id, p.full_name as student_name, p.email, i.title as internship_title,
               a.status, a.offer_letter_id, a.start_date, a.end_date, a.applied_at
        FROM applications a
        JOIN profiles p ON a.user_id = p.id
        JOIN internships i ON a.internship_id = i.id
    """)
    apps = [dict(r) for r in cursor.fetchall()]
    for a in apps:
        res = send_to_google_sheets('APPLICATION', a)
        if res.get('success'):
            synced_counts['applications'] += 1

    # 3. Certificates & Payments
    cursor.execute("""
        SELECT c.id as certificate_id, p.full_name as student_name, p.email,
               a.offer_letter_id, c.is_verified_paid, c.issued_at
        FROM certificates c
        JOIN applications a ON c.application_id = a.id
        JOIN profiles p ON a.user_id = p.id
    """)
    certs = [dict(r) for r in cursor.fetchall()]
    for c in certs:
        res = send_to_google_sheets('CERTIFICATE', c)
        if res.get('success'):
            synced_counts['certificates'] += 1

    conn.close()
    log_success(f"Synced to Google Sheets: {synced_counts}")
    return synced_counts
