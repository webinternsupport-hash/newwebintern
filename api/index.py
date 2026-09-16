import os
import sys

# Add root directory to sys.path so app and submodules can be imported properly on Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Create app with error handling for Vercel environment
try:
    from app import create_app
    app = create_app()
except Exception as e:
    # Log the error but don't crash
    print(f"WARNING: Error creating app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    
    # Create a minimal fallback app that at least responds
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def health():
        return jsonify({'error': 'App initialization failed', 'message': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

# Export app for Vercel Serverless Function WSGI runner
__all__ = ['app']


