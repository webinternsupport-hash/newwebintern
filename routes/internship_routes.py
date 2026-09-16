from flask import Blueprint, request, jsonify
from database import get_db_connection

internship_bp = Blueprint('internship_bp', __name__)

@internship_bp.route('/api/internships', methods=['GET'])
def get_internships():
    sector_slug = request.args.get('sector', '').strip()
    search = request.args.get('q', '').strip()
    featured = request.args.get('featured', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT i.*, s.name as sector_name, s.slug as sector_slug
        FROM internships i
        LEFT JOIN sectors s ON i.sector_id = s.id
        WHERE i.active = 1
    """
    params = []
    
    if sector_slug:
        query += " AND s.slug = ?"
        params.append(sector_slug)
        
    if search:
        query += " AND (i.title LIKE ? OR i.short_description LIKE ? OR i.skills_tools LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if featured in ('1', 'true', 'True'):
        query += " AND i.is_featured = 1"
        
    query += " ORDER BY i.is_featured DESC, i.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    internships = [dict(r) for r in rows]
    
    # Total count query
    count_query = "SELECT COUNT(*) FROM internships i LEFT JOIN sectors s ON i.sector_id = s.id WHERE i.active = 1"
    count_params = []
    if sector_slug:
        count_query += " AND s.slug = ?"
        count_params.append(sector_slug)
    if search:
        count_query += " AND (i.title LIKE ? OR i.short_description LIKE ? OR i.skills_tools LIKE ?)"
        count_params.extend([wildcard, wildcard, wildcard])
    if featured in ('1', 'true', 'True'):
        count_query += " AND i.is_featured = 1"
        
    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'internships': internships,
        'total': total_count,
        'page': page,
        'limit': limit
    }), 200

@internship_bp.route('/api/internships/<slug>', methods=['GET'])
def get_internship_detail(slug):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT i.*, s.name as sector_name, s.slug as sector_slug
        FROM internships i
        LEFT JOIN sectors s ON i.sector_id = s.id
        WHERE i.slug = ? AND i.active = 1
    """, (slug,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Internship program not found'}), 404
        
    internship = dict(row)
    
    # Fetch weekly task blueprints
    cursor.execute("""
        SELECT * FROM internship_tasks 
        WHERE internship_id = ? 
        ORDER BY week_number ASC
    """, (internship['id'],))
    tasks = [dict(t) for t in cursor.fetchall()]
    
    internship['tasks'] = tasks
    conn.close()
    
    return jsonify({'internship': internship}), 200
