from flask import Blueprint, jsonify
from database import get_db_connection

sector_bp = Blueprint('sector_bp', __name__)

@sector_bp.route('/api/sectors', methods=['GET'])
def get_sectors():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, COUNT(i.id) as internship_count
        FROM sectors s
        LEFT JOIN internships i ON s.id = i.sector_id AND i.active = 1
        GROUP BY s.id
        ORDER BY s.name ASC
    """)
    rows = cursor.fetchall()
    sectors = [dict(r) for r in rows]
    conn.close()
    
    return jsonify({'sectors': sectors}), 200

@sector_bp.route('/api/sectors/<slug>', methods=['GET'])
def get_sector_by_slug(slug):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sectors WHERE slug = ?", (slug,))
    sector = cursor.fetchone()
    
    if not sector:
        conn.close()
        return jsonify({'error': 'Sector not found'}), 404
        
    cursor.execute("SELECT * FROM internships WHERE sector_id = ? AND active = 1 ORDER BY title ASC", (sector['id'],))
    internships = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        'sector': dict(sector),
        'internships': internships
    }), 200
