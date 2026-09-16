import uuid
import requests
from database import get_db_connection
from config import Config
from utils.logger import log_info, log_success, log_error

def seed_empty_local_tables(conn):
    cursor = conn.cursor()
    
    # 1. Organization Settings
    cursor.execute("SELECT COUNT(*) FROM organization_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO organization_settings (key, value) VALUES ('site_name', 'Web Intern Platform')")
        cursor.execute("INSERT OR REPLACE INTO organization_settings (key, value) VALUES ('support_email', 'support@webintern.in')")
        cursor.execute("INSERT OR REPLACE INTO organization_settings (key, value) VALUES ('version', '2.0.26')")
    
    # 2. Newsletter Subscribers
    cursor.execute("SELECT COUNT(*) FROM newsletter_subscribers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO newsletter_subscribers (id, email) VALUES (?, ?)", 
                       (str(uuid.uuid4()), 'subscriber_test@webintern.in'))
    
    # 3. Contact Messages
    cursor.execute("SELECT COUNT(*) FROM contact_messages")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO contact_messages (id, name, email, subject, message) VALUES (?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), 'Alex Test', 'alex.test@example.com', 'Internship Inquiry', 'Testing Supabase integration for contact messages.'))
        
    # 4. Audit Logs
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM profiles LIMIT 1")
        prof = cursor.fetchone()
        pid = prof['id'] if prof else None
        cursor.execute("INSERT INTO audit_logs (id, user_id, action, details, ip_address) VALUES (?, ?, ?, ?, ?)",
                       (str(uuid.uuid4()), pid, 'SUPABASE_SYNC_TEST', 'Initial full database verification sync', '127.0.0.1'))
        
    # 5. Password Resets
    cursor.execute("SELECT COUNT(*) FROM password_resets")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO password_resets (id, email, token, expires_at, used) VALUES (?, ?, ?, '2026-12-31 23:59:59', 0)",
                       (str(uuid.uuid4()), 'teststudent@college.edu', 'test_password_reset_token_999'))
        
    # 6. Notifications
    cursor.execute("SELECT COUNT(*) FROM notifications")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM profiles LIMIT 1")
        prof = cursor.fetchone()
        if prof:
            cursor.execute("INSERT INTO notifications (id, user_id, title, message, is_read) VALUES (?, ?, ?, ?, 0)",
                           (str(uuid.uuid4()), prof['id'], 'Welcome to Web Intern', 'Your profile and database account are fully verified.'))

    conn.commit()

def sync_all_17_tables_to_supabase():
    url = Config.SUPABASE_URL
    service_key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY
    if not url or not service_key:
        print("[ERROR] Supabase credentials not configured in environment.")
        return

    headers = {
        'apikey': service_key,
        'Authorization': f"Bearer {service_key}",
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    conn = get_db_connection()
    seed_empty_local_tables(conn)

    # Dependency ordered table list
    tables_in_order = [
        'profiles',
        'admins',
        'sectors',
        'products',
        'organization_settings',
        'newsletter_subscribers',
        'contact_messages',
        'audit_logs',
        'password_resets',
        'internships',
        'internship_tasks',
        'applications',
        'certificates',
        'payments',
        'documents',
        'master_internships',
        'notifications'
    ]

    print("=== SYNCING ALL 17 TABLES TO SUPABASE PostgREST API ===")
    results = {}

    for table_name in tables_in_order:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = [dict(r) for r in cursor.fetchall()]
        
        if not rows:
            print(f"Table {table_name}: No local rows to sync.")
            results[table_name] = 0
            continue

        # Format rows for Supabase JSON payload
        formatted_rows = []
        for row in rows:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, bytes):
                    clean_row[k] = v.decode('utf-8', errors='ignore')
                elif v is not None:
                    clean_row[k] = v
                else:
                    clean_row[k] = None
            formatted_rows.append(clean_row)

        # Batch upsert into Supabase PostgREST
        try:
            # Post in batches of 50
            batch_size = 50
            synced_count = 0
            for i in range(0, len(formatted_rows), batch_size):
                batch = formatted_rows[i:i+batch_size]
                resp = requests.post(f"{url}/rest/v1/{table_name}", json=batch, headers=headers, timeout=15)
                if resp.status_code in (200, 201, 204):
                    synced_count += len(batch)
                else:
                    print(f"  [ERR] {table_name} batch {i}: HTTP {resp.status_code} - {resp.text[:150]}")
            
            print(f"  [SUCCESS] {table_name}: Synced {synced_count}/{len(rows)} records to Supabase.")
            results[table_name] = synced_count
        except Exception as ex:
            print(f"  [EXCEPTION] {table_name}: {ex}")
            results[table_name] = 0

    conn.close()

    print("\n=== VERIFYING SUPABASE ROW COUNTS FOR ALL 17 TABLES ===")
    for table_name in tables_in_order:
        try:
            r = requests.get(f"{url}/rest/v1/{table_name}?select=id", headers=headers, timeout=5)
            if r.status_code != 200 and table_name == 'organization_settings':
                r = requests.get(f"{url}/rest/v1/{table_name}?select=key", headers=headers, timeout=5)
            if r.status_code == 200:
                count = len(r.json())
                print(f"  ✓ Supabase Table '{table_name}': {count} rows verified.")
            else:
                print(f"  ✗ Supabase Table '{table_name}': Status {r.status_code} - {r.text[:100]}")
        except Exception as e:
            print(f"  ✗ Supabase Table '{table_name}': Exception {e}")

if __name__ == '__main__':
    sync_all_17_tables_to_supabase()
