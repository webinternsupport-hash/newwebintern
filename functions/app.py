"""
Netlify Functions handler for Flask app
Converts Netlify invocation to Flask WSGI
"""
import os
import sys
import traceback
from urllib.parse import urlparse, parse_qs

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify

def create_minimal_app():
    """Minimal fallback Flask app"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Netlify is running'}), 200
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Web Intern API'}), 200
    
    return app

# Load or create app
app = None
try:
    from app import create_app
    app = create_app()
    print("[SUCCESS] Full Flask app loaded", file=sys.stderr)
except Exception as e:
    print(f"[ERROR] Failed to load app: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    app = create_minimal_app()

if app is None:
    app = create_minimal_app()

def handler(event, context):
    """Netlify Functions handler"""
    try:
        # Parse the incoming request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_string = event.get('rawQueryString', '')
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # Create WSGI environ
        environ = {
            'REQUEST_METHOD': http_method,
            'SCRIPT_NAME': '',
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'SERVER_NAME': headers.get('host', 'localhost'),
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': None,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # Add headers
        for header_name, header_value in headers.items():
            header_name_upper = header_name.upper().replace('-', '_')
            if header_name_upper not in ('HOST', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{header_name_upper}'] = header_value
            elif header_name_upper == 'CONTENT_TYPE':
                environ['CONTENT_TYPE'] = header_value
            elif header_name_upper == 'CONTENT_LENGTH':
                environ['CONTENT_LENGTH'] = header_value
        
        # Collect response
        status_code = 200
        response_headers = {}
        response_body = []
        
        def start_response(status, response_headers_list):
            nonlocal status_code, response_headers
            status_code = int(status.split()[0])
            response_headers = dict(response_headers_list)
        
        # Call Flask app
        app_iter = app(environ, start_response)
        
        # Collect body
        try:
            for data in app_iter:
                if data:
                    response_body.append(data)
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()
        
        body_str = b''.join(response_body).decode('utf-8', errors='ignore')
        
        return {
            'statusCode': status_code,
            'headers': response_headers,
            'body': body_str,
            'isBase64Encoded': False
        }
    
    except Exception as e:
        print(f"[ERROR] Handler error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            'statusCode': 500,
            'body': str(e)
        }
