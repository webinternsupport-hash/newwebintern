import os
import shutil
import tempfile
from dotenv import load_dotenv

# Ensure .env is explicitly loaded from root directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

def get_sqlite_db_path():
    root_db = os.path.join(os.path.dirname(__file__), "webintern.db")
    
    # Detect Vercel / AWS Lambda / Serverless read-only environment
    is_serverless = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    
    if is_serverless:
        tmp_db = os.path.join(tempfile.gettempdir(), "webintern.db")
        try:
            if os.path.exists(root_db):
                root_size = os.path.getsize(root_db)
                if not os.path.exists(tmp_db) or os.path.getsize(tmp_db) < root_size:
                    shutil.copy2(root_db, tmp_db)
                return tmp_db
        except Exception as e:
            print(f"Warning: Failed to copy DB to /tmp: {e}")
            if os.path.exists(root_db):
                return root_db
            return tmp_db
        return tmp_db
    
    return root_db

class Config:
    # JWT Configuration
    SECRET_KEY = (os.getenv("JWT_SECRET") or "webintern_jwt_secret_key_2026_secure_token_982347").strip()
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # Supabase credentials
    SUPABASE_URL = (os.getenv("SUPABASE_URL") or "https://fzmdeigwxiesegvtuafk.supabase.co").strip()
    SUPABASE_ANON_KEY = (os.getenv("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6bWRlaWd3eGllc2VndnR1YWZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0MjA2NDAsImV4cCI6MjEwMzk5NjY0MH0.aqk90jQu4yBCgc0wi9zA0cMHf5XZ31OPVc3hcED0_J8").strip()
    SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6bWRlaWd3eGllc2VndnR1YWZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODQyMDY0MCwiZXhwIjoyMTAzOTk2NjQwfQ.osKcbobbZPLz7RpO0zVgyHbIPJC2l6QDF6MBQ-W0uTA").strip()

    # Google OAuth credentials
    GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()

    # Resend Email API
    RESEND_API_KEY = (os.getenv("RESEND_API_KEY") or "").strip()

    # Razorpay Integration
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    
    CERTIFICATE_PRICE_INR = int(os.getenv("CERTIFICATE_PRICE_INR", 199))
    CERTIFICATE_PRICE_PAISE = int(os.getenv("CERTIFICATE_PRICE_PAISE", 19900))
    
    # Google Sheets Webhook
    GOOGLE_SHEETS_WEBHOOK_URL = (os.getenv("GOOGLE_SHEETS_WEBHOOK_URL") or "").strip()



    # DB Fallback Path
    SQLITE_DB_PATH = get_sqlite_db_path()

    # Document Template & Storage Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PUBLIC_DIR = os.path.join(BASE_DIR, "public")
    TEMPLATE_DIR = os.path.join(PUBLIC_DIR, "templates")

    OFFER_LETTER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "offer-letter-template.png")
    CERTIFICATE_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "certificate-template.png")

    OFFER_LETTER_TEMPLATE_URL = "/templates/offer-letter-template.png"
    CERTIFICATE_TEMPLATE_URL = "/templates/certificate-template.png"

    STORAGE_DIR = os.path.join(BASE_DIR, "storage")
    GENERATED_OFFERS_DIR = os.path.join(STORAGE_DIR, "generated", "offers")
    GENERATED_CERTIFICATES_DIR = os.path.join(STORAGE_DIR, "generated", "certificates")

    DOCUMENT_TEMPLATES = {
        "offer_letter": {
            "path": OFFER_LETTER_TEMPLATE_PATH,
            "url": OFFER_LETTER_TEMPLATE_URL,
            "filename": "offer-letter-template.png",
        },
        "certificate": {
            "path": CERTIFICATE_TEMPLATE_PATH,
            "url": CERTIFICATE_TEMPLATE_URL,
            "filename": "certificate-template.png",
        }
    }

