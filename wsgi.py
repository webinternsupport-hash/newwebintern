"""
WSGI entry point for production deployment on Vercel.
This file is used by the Vercel Python runtime to start the application.
"""

import os
import sys
import traceback

try:
    from app import create_app
    app = create_app()
except Exception as e:
    print(f"CRITICAL ERROR during app creation: {e}", file=sys.stderr)
    traceback.print_exc()
    # Fallback app for debugging
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return jsonify({'error': f'App initialization failed: {str(e)}'}), 500

# For local testing
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
