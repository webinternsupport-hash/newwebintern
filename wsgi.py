"""
WSGI entry point for production deployment on Vercel.
This file is used by the Vercel Python runtime to start the application.
"""

import os
import sys
import traceback

# Minimal Flask app for Vercel
from flask import Flask, jsonify

def create_minimal_app():
    """Create a minimal Flask app for testing"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Minimal health check'}), 200
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Web Intern API - Minimal Version'}), 200
    
    return app

# Try to load full app, fall back to minimal
try:
    from app import create_app
    app = create_app()
    print("[SUCCESS] Full app loaded", file=sys.stderr)
except ImportError as e:
    print(f"[WARNING] Full app import failed: {e}", file=sys.stderr)
    print("Falling back to minimal app", file=sys.stderr)
    app = create_minimal_app()
except Exception as e:
    print(f"[ERROR] App creation failed: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    app = create_minimal_app()

# Vercel requires 'app' to be exported at module level
__all__ = ['app']

# For local testing
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
