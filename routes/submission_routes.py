import os
import uuid
import datetime
from flask import Blueprint, request, jsonify, g, send_file
from werkzeug.utils import secure_filename
from database import get_db_connection
from utils.auth import jwt_required
from config import Config
from utils.logger import log_info, log_success, log_error

submission_bp = Blueprint('submission_bp', __name__)

@submission_bp.route('/api/submissions/upload', methods=['POST'])
@jwt_required
def upload_submission():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part provided'}), 400
        
    file = request.files['file']
    application_id = request.form.get('application_id')
    week_number = request.form.get('week_number')
    
    if not application_id or not week_number:
        return jsonify({'error': 'application_id and week_number are required'}), 400
        
    try:
        week_num = int(week_number)
    except ValueError:
        return jsonify({'error': 'week_number must be an integer (1-4)'}), 400
        
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    original_filename = secure_filename(file.filename)
    if not original_filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed for task submissions'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check application ownership
    cursor.execute("SELECT * FROM applications WHERE id = ? AND (user_id = ? OR LOWER(user_id) = ?)", (application_id, g.user_id, g.user_email))
    app_record = cursor.fetchone()
    if not app_record:
        conn.close()
        return jsonify({'error': 'Application not found or unauthorized'}), 403

    # Generate safe unique filename
    file_id = str(uuid.uuid4())[:8]
    saved_filename = f"{application_id}_week_{week_num}_{file_id}_{original_filename}"
    file_path = os.path.join(Config.SUBMISSIONS_DIR, saved_filename)
    
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    file_url = f"/api/submissions/file/{saved_filename}"
    
    # Check existing submission for this week
    cursor.execute("SELECT id FROM submissions WHERE application_id = ? AND week_number = ?", (application_id, week_num))
    existing = cursor.fetchone()
    
    if existing:
        sub_id = existing['id']
        cursor.execute("""
            UPDATE submissions 
            SET file_url = ?, original_file_name = ?, file_size = ?, status = 'pending', submitted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (file_url, original_filename, file_size, sub_id))
    else:
        sub_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO submissions (
                id, application_id, week_number, file_url, original_file_name, file_size, status, max_marks, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 10, CURRENT_TIMESTAMP)
        """, (sub_id, application_id, week_num, file_url, original_filename, file_size))
        
    conn.commit()
    conn.close()
    
    log_success(f"Uploaded Week {week_num} submission for App {application_id}: {original_filename}")
    return jsonify({
        'message': f'Week {week_num} task submitted successfully!',
        'submission_id': sub_id,
        'file_url': file_url,
        'week_number': week_num,
        'status': 'pending'
    }), 201

@submission_bp.route('/api/submissions/<app_id>', methods=['GET'])
@jwt_required
def get_submissions(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM submissions WHERE application_id = ? ORDER BY week_number ASC", (app_id,))
    submissions = [dict(s) for s in cursor.fetchall()]
    conn.close()
    
    return jsonify({'submissions': submissions}), 200

@submission_bp.route('/api/submissions/file/<filename>', methods=['GET'])
def serve_submission_file(filename):
    file_path = os.path.join(Config.SUBMISSIONS_DIR, secure_filename(filename))
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, mimetype='application/pdf')
