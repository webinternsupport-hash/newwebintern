import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env file if available
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

class Config:
    BASE_DIR = BASE_DIR
    APP_URL = os.environ.get('APP_URL', 'http://127.0.0.1:5000')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'webintern-secret-key-production-2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.environ.get('JWT_SECRET', 'webintern-jwt-secret-key-super-secure'))
    JWT_EXPIRATION_HOURS = 24 * 7  # 7 days
    
    # Check if running in Vercel or read-only environment
    IS_VERCEL = bool(os.environ.get('VERCEL')) or not os.access(BASE_DIR, os.W_OK)
    
    DB_PATH = os.environ.get('DATABASE_URL', os.path.join('/tmp', 'webintern.db') if IS_VERCEL else os.path.join(BASE_DIR, 'webintern.db'))
    
    UPLOAD_FOLDER = os.path.join('/tmp', 'storage') if IS_VERCEL else os.path.join(BASE_DIR, 'storage')
    OFFER_LETTERS_DIR = os.path.join(UPLOAD_FOLDER, 'offer_letters')
    CERTIFICATES_DIR = os.path.join(UPLOAD_FOLDER, 'certificates')
    SUBMISSIONS_DIR = os.path.join(UPLOAD_FOLDER, 'submissions')
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit for uploads
    
    # Supabase Credentials
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    
    # Razorpay Integration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    CERTIFICATE_FEE_INR = 199
    
    # Resend Email Integration
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', os.environ.get('FROM_EMAIL', 'notifications@webintern.in'))
    SUPPORT_EMAIL = os.environ.get('RESEND_SUPPORT_EMAIL', 'support@webintern.in')
    
    # Google Sheets Webhook
    GOOGLE_SHEETS_WEBHOOK_URL = os.environ.get('GOOGLE_SHEETS_WEBHOOK_URL', '')

    @staticmethod
    def init_app(app):
        os.makedirs(Config.OFFER_LETTERS_DIR, exist_ok=True)
        os.makedirs(Config.CERTIFICATES_DIR, exist_ok=True)
        os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)

