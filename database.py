import sqlite3
import os
from config import Config
from utils.logger import log_info, log_success, log_error

def get_db_connection():
    db_path = Config.DB_PATH
    if getattr(Config, 'IS_VERCEL', False):
        if db_path != os.path.join('/tmp', 'webintern.db'):
            db_path = os.path.join('/tmp', 'webintern.db')
        source_db = os.path.join(Config.BASE_DIR, 'webintern.db')
        if not os.path.exists(db_path) and os.path.exists(source_db):
            try:
                import shutil
                shutil.copy2(source_db, db_path)
            except Exception as e:
                pass
    conn = sqlite3.connect(db_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        _init_db_tables()
    except Exception as e:
        log_error(f"Error initializing database: {e}")

def _init_db_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try enabling WAL mode for local, DELETE mode for Vercel serverless
    if getattr(Config, 'IS_VERCEL', False):
        try:
            cursor.execute("PRAGMA journal_mode=DELETE;")
        except Exception:
            pass
    else:
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            mode = cursor.fetchone()[0]
            log_info(f"SQLite journal mode set to: {mode}")
        except Exception as e:
            log_error(f"Failed to set WAL journal mode, falling back to DELETE mode: {e}")
            try:
                cursor.execute("PRAGMA journal_mode=DELETE;")
            except Exception:
                pass

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Profiles (Student Accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
      id VARCHAR(36) PRIMARY KEY,
      full_name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      phone TEXT,
      phone_country_code TEXT DEFAULT '+91',
      college TEXT,
      department TEXT,
      degree TEXT,
      password_hash TEXT,
      auth_provider TEXT DEFAULT 'email',
      mobile TEXT,
      terms_accepted BOOLEAN DEFAULT FALSE,
      marketing_opt_in BOOLEAN DEFAULT FALSE,
      google_account_id TEXT,
      sync_enabled BOOLEAN DEFAULT TRUE,
      last_sync_time TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Admins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
      id VARCHAR(36) PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      full_name TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Sectors (Domain Tracks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sectors (
      id VARCHAR(36) PRIMARY KEY,
      name TEXT NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      icon_url TEXT,
      description TEXT
    );
    """)

    # 4. Internships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS internships (
      id VARCHAR(36) PRIMARY KEY,
      sector_id VARCHAR(36) REFERENCES sectors(id),
      title TEXT NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      short_description TEXT,
      full_description TEXT,
      duration_weeks INT DEFAULT 4,
      mode TEXT DEFAULT 'Virtual',
      cover_image_url TEXT,
      company_name TEXT DEFAULT 'Web Intern Platform',
      location TEXT DEFAULT 'Virtual / Remote',
      guide_name TEXT DEFAULT 'Dr. A. K. Sharma (Technical Director)',
      skills_tools TEXT DEFAULT 'Python, Web Development, Analytics, Cloud',
      tasks_projects TEXT DEFAULT 'Industry Capstone Project & Weekly Deliverables',
      project_name TEXT DEFAULT 'Enterprise Internship Project',
      certificate_eligible BOOLEAN DEFAULT TRUE,
      active BOOLEAN DEFAULT TRUE,
      internship_emoji TEXT DEFAULT '💼',
      is_featured BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Internship Tasks (Weekly Modules)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS internship_tasks (
      id VARCHAR(36) PRIMARY KEY,
      internship_id VARCHAR(36) REFERENCES internships(id) ON DELETE CASCADE,
      week_number INT NOT NULL,
      title TEXT NOT NULL,
      objective TEXT,
      deliverables TEXT,
      key_steps TEXT,
      evaluation_criteria TEXT
    );
    """)

    # 6. Applications (Enrollments)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
      id VARCHAR(36) PRIMARY KEY,
      user_id VARCHAR(36) REFERENCES profiles(id) ON DELETE CASCADE,
      internship_id VARCHAR(36) REFERENCES internships(id),
      status TEXT DEFAULT 'active',
      offer_letter_sent BOOLEAN DEFAULT FALSE,
      start_date TEXT,
      end_date TEXT,
      offer_letter_id TEXT,
      certificate_id TEXT,
      completion_status TEXT DEFAULT 'pending',
      google_sync_status TEXT DEFAULT 'not_synced',
      last_synced_at TIMESTAMP,
      applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Submissions (Student PDF Work Uploads)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
      id VARCHAR(36) PRIMARY KEY,
      application_id VARCHAR(36) REFERENCES applications(id) ON DELETE CASCADE,
      week_number INT NOT NULL,
      file_url TEXT,
      original_file_name TEXT,
      file_size INTEGER,
      status TEXT DEFAULT 'pending',
      feedback TEXT,
      marks REAL,
      max_marks REAL DEFAULT 10,
      graded_by TEXT,
      graded_at TEXT,
      submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      reviewed_at TIMESTAMP
    );
    """)

    # 8. Certificates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
      id VARCHAR(36) PRIMARY KEY,
      application_id VARCHAR(36) REFERENCES applications(id),
      certificate_url TEXT,
      is_verified_paid BOOLEAN DEFAULT FALSE,
      issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Payments (Razorpay Orders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
      id VARCHAR(36) PRIMARY KEY,
      user_id VARCHAR(36) REFERENCES profiles(id),
      certificate_id VARCHAR(36) REFERENCES certificates(id),
      product_id VARCHAR(36) REFERENCES products(id),
      razorpay_order_id TEXT NOT NULL,
      razorpay_payment_id TEXT,
      razorpay_signature TEXT,
      amount_inr INT NOT NULL DEFAULT 199,
      status TEXT DEFAULT 'created',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10. Documents (Tracking Issued PDF Documents)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
      id VARCHAR(36) PRIMARY KEY,
      application_id VARCHAR(36) NOT NULL,
      student_id VARCHAR(36) NOT NULL,
      document_type TEXT NOT NULL,
      document_number TEXT UNIQUE NOT NULL,
      file_path TEXT,
      status TEXT DEFAULT 'ISSUED',
      email_status TEXT DEFAULT 'PENDING',
      email_message_id TEXT,
      email_sent_at TIMESTAMP,
      sheets_synced BOOLEAN DEFAULT FALSE,
      sheets_synced_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 11. Master Internships (Unified Master Academic Records)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master_internships (
      id VARCHAR(36) PRIMARY KEY,
      student_full_name TEXT NOT NULL,
      student_email TEXT NOT NULL,
      student_mobile TEXT,
      college_name TEXT NOT NULL,
      degree TEXT NOT NULL,
      department TEXT NOT NULL,
      internship_position TEXT NOT NULL,
      internship_domain TEXT,
      internship_start_date TEXT NOT NULL,
      internship_end_date TEXT NOT NULL,
      project_title TEXT NOT NULL,
      mentor_name TEXT NOT NULL,
      offer_id TEXT UNIQUE NOT NULL,
      certificate_id TEXT UNIQUE NOT NULL,
      user_id VARCHAR(36),
      application_id VARCHAR(36),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 12. Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
      id VARCHAR(36) PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT,
      price_inr INT DEFAULT 199,
      active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 13. Password Resets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
      id VARCHAR(36) PRIMARY KEY,
      email TEXT NOT NULL,
      token TEXT NOT NULL,
      expires_at TIMESTAMP NOT NULL,
      used BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 14. Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
      id VARCHAR(36) PRIMARY KEY,
      user_id VARCHAR(36),
      action TEXT NOT NULL,
      details TEXT,
      ip_address TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 15. Organization Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organization_settings (
      key TEXT PRIMARY KEY,
      value TEXT,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 16. Contact Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
      id VARCHAR(36) PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      subject TEXT,
      message TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 17. Newsletter Subscribers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
      id VARCHAR(36) PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 18. Testimonials
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS testimonials (
      id VARCHAR(36) PRIMARY KEY,
      student_name TEXT NOT NULL,
      college TEXT,
      rating INT DEFAULT 5,
      review TEXT NOT NULL,
      avatar_url TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 19. Site Stats
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS site_stats (
      id VARCHAR(36) PRIMARY KEY,
      metric_key TEXT UNIQUE NOT NULL,
      metric_value TEXT NOT NULL,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 20. Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
      id VARCHAR(36) PRIMARY KEY,
      user_id VARCHAR(36) REFERENCES profiles(id) ON DELETE CASCADE,
      title TEXT NOT NULL,
      message TEXT NOT NULL,
      is_read BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_internship ON applications(internship_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_app ON submissions(application_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_certificates_app ON certificates(application_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_student ON documents(student_id);")

    conn.commit()
    conn.close()
    log_success("Database initialized with 20 tables & indexes successfully.")


