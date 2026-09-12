"""
Netlify Functions handler for Flask app
"""
import os
import sys
import traceback
from flask import Flask, jsonify

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_minimal_app():
    """Create minimal fallback app"""
    minimal_app = Flask(__name__)
    
    @minimal_app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Netlify Functions running'}), 200
    
    @minimal_app.route('/')
    def index():
        return jsonify({'message': 'Web Intern API - Netlify'}), 200
    
    return minimal_app

# Initialize app
app = None

try:
    from app import create_app
    app = create_app()
    print("[SUCCESS] Full Flask app loaded", file=sys.stderr)
except Exception as e:
    print(f"[WARNING] Failed to load full app: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    app = create_minimal_app()
    print("[FALLBACK] Using minimal app", file=sys.stderr)

if app is None:
    app = create_minimal_app()

# Netlify Functions handler
def handler(event, context):
    """Netlify Functions handler"""
    # This is a wrapper for compatibility
    return {
        "statusCode": 200,
        "body": "Use Flask routing instead"
    }
