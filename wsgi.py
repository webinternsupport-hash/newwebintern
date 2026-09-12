"""
WSGI entry point for Vercel deployment
"""
import os
import sys
import traceback
from flask import Flask, jsonify

# Create minimal fallback app
def create_minimal_app():
    minimal_app = Flask(__name__)
    
    @minimal_app.route('/health')
    def health():
        return jsonify({'status': 'ok'}), 200
    
    @minimal_app.route('/')
    def index():
        return jsonify({'message': 'API is running'}), 200
    
    return minimal_app

# Initialize app - Vercel needs this at module level
app = None

try:
    from app import create_app
    app = create_app()
    sys.stderr.write("[SUCCESS] Full Flask app loaded\n")
except Exception as e:
    sys.stderr.write(f"[WARNING] Failed to load full app: {e}\n")
    traceback.print_exc(file=sys.stderr)
    app = create_minimal_app()
    sys.stderr.write("[FALLBACK] Using minimal app\n")

# Ensure app exists
if app is None:
    app = create_minimal_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
