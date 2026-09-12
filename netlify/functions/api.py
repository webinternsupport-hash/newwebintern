"""
Netlify Functions handler for Flask app
"""
import os
import sys
import traceback
import json
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify

def create_minimal_app():
    """Minimal fallback Flask app"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Netlify is running'}), 200
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Web Intern API on Netlify'}), 200
    
    return app

# Load or create app
app = None
try:
    from app import create_app
    app = create_app()
    sys.stderr.write("[SUCCESS] Full Flask app loaded\n")
except Exception as e:
    sys.stderr.write(f"[ERROR] Failed to load app: {e}\n")
    traceback.print_exc(file=sys.stderr)
    app = create_minimal_app()

if app is None:
    app = create_minimal_app()

def handler(event, context):
    """Netlify Functions handler - converts event to WSGI"""
    try:
        http_method = event.get('httpMethod', 'GET').upper()
        path = event.get('path', '/')
        query_string = event.get('rawQueryString', '')
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # Create WSGI environ dict
        environ = {
            'REQUEST_METHOD': http_method,
            'SCRIPT_NAME': '',
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': headers.get('content-length', ''),
            'SERVER_NAME': headers.get('host', 'localhost').split(':')[0],
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(body.encode('utf-8') if isinstance(body, str) else body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': True,
        }
        
        # Add HTTP headers
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Response collection
        status_code = 200
        response_headers = []
        
        def start_response(status, headers_list):
            nonlocal status_code
            status_code = int(status.split()[0])
            return lambda s: None
        
        # Call Flask WSGI app
        response = app(environ, start_response)
        
        # Collect response body
        body_parts = []
        for data in response:
            if data:
                body_parts.append(data)
        
        response_body = b''.join(body_parts)
        
        if hasattr(response, 'close'):
            response.close()
        
        # Build response
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': response_body.decode('utf-8', errors='ignore') if isinstance(response_body, bytes) else response_body
        }
    
    except Exception as e:
        sys.stderr.write(f"[ERROR] Handler failed: {e}\n")
        traceback.print_exc(file=sys.stderr)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
