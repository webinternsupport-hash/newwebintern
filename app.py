import os
import sys

# Ensure UTF-8 stdout encoding for Windows console safe logging
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from flask import Flask, send_from_directory, jsonify, request
from config import Config
from database import init_db
from routes.auth_routes import auth_bp
from routes.sector_routes import sector_bp
from routes.internship_routes import internship_bp
from routes.application_routes import application_bp
from routes.submission_routes import submission_bp
from routes.certificate_routes import certificate_bp
from routes.payment_routes import payment_bp
from routes.admin_routes import admin_bp
from routes.referral_routes import referral_bp
from utils.logger import log_info, log_success

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)
    
    try:
        Config.init_app(app)
    except Exception as e:
        print(f"WARNING: Config.init_app() failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    # Initialize database tables
    try:
        init_db()
    except Exception as e:
        print(f"WARNING: init_db() failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    # Register Blueprints with error handling
    blueprints = [
        ('auth', auth_bp),
        ('sector', sector_bp),
        ('internship', internship_bp),
        ('application', application_bp),
        ('submission', submission_bp),
        ('certificate', certificate_bp),
        ('payment', payment_bp),
        ('admin', admin_bp),
        ('referral', referral_bp),
    ]
    
    for bp_name, bp in blueprints:
        try:
            app.register_blueprint(bp)
            print(f"INFO: Registered blueprint: {bp_name}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Failed to register blueprint '{bp_name}': {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    # Serve SPA index
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    @app.route('/api/health', methods=['GET'])
    def health_check():
        from utils.supabase_client import check_supabase_connection
        sp_status = check_supabase_connection()
        return jsonify({
            'status': 'healthy',
            'database': 'sqlite',
            'supabase': sp_status
        }), 200

    @app.route('/api/supabase/status', methods=['GET'])
    def supabase_status():
        from utils.supabase_client import check_supabase_connection
        sp_status = check_supabase_connection()
        return jsonify(sp_status), 200 if sp_status.get('connected') else 500

    @app.route('/api/supabase/create-account', methods=['POST'])
    def supabase_create_account():
        from utils.supabase_client import create_supabase_user, login_supabase_user
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        password = data.get('password', '')
        metadata = data.get('metadata', {})

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        res = create_supabase_user(email, password, user_metadata=metadata)
        if res.get('success'):
            login_res = login_supabase_user(email, password)
            return jsonify({
                'message': 'Supabase account created and verified successfully',
                'user': res.get('user'),
                'session_login_verified': login_res.get('success')
            }), 201
        else:
            return jsonify({'error': res.get('error')}), 400

    @app.route('/api/google-sheets/test', methods=['GET', 'POST'])
    def google_sheets_test():
        from utils.google_sheets import send_to_google_sheets
        from config import Config

        test_payload = {
            'timestamp': '2026-09-16 07:22:00',
            'full_name': 'Test Google Sheets User',
            'email': 'sheets_test@webintern.in',
            'status': 'VERIFIED_CONNECTED',
            'webhook_url': Config.GOOGLE_SHEETS_WEBHOOK_URL
        }
        res = send_to_google_sheets('TEST_PING', test_payload)
        return jsonify({
            'message': 'Google Sheets Webhook test executed',
            'result': res
        }), 200 if res.get('success') else 500

    @app.route('/api/google-sheets/sync-all', methods=['POST'])
    def google_sheets_sync_all():
        from utils.google_sheets import sync_all_existing_data_to_google_sheets
        counts = sync_all_existing_data_to_google_sheets()
        return jsonify({
            'message': 'All existing data synced to Google Sheets Webhook',
            'synced_counts': counts
        }), 200
        
    @app.errorhandler(404)
    def not_found(e):
        # Fallback to SPA index for non-API routes
        if not request.path.startswith('/api/'):
            return send_from_directory('static', 'index.html')
        return jsonify({'error': 'Endpoint not found'}), 404
        
    return app

# Only run the development server if this is the main module (local development)
if __name__ == '__main__':
    app = create_app()
    log_success("Starting Web Intern Platform server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
