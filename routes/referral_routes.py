import uuid
import datetime
from urllib.parse import quote
from flask import Blueprint, request, jsonify, g
from database import get_db_connection
from utils.auth import jwt_required
from config import Config
from utils.logger import log_info, log_success, log_error

referral_bp = Blueprint('referral_bp', __name__)

def generate_user_referral_code(cursor, user_id):
    """
    Generates a unique WIREF-XXXXXX code for a user if missing.
    """
    cursor.execute("SELECT referral_code FROM profiles WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row['referral_code']:
        return row['referral_code']
        
    code = f"WIREF-{uuid.uuid4().hex[:6].upper()}"
    cursor.execute("UPDATE profiles SET referral_code = ? WHERE id = ?", (code, user_id))
    return code

@referral_bp.route('/api/referrals/my-stats', methods=['GET'])
@jwt_required
def get_my_referral_stats():
    user_id = g.user_id
    user_email = (g.user_email or '').lower().strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch profile & ensure referral code exists
    cursor.execute("SELECT id, full_name, email, referral_code FROM profiles WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user and user_email:
        cursor.execute("SELECT id, full_name, email, referral_code FROM profiles WHERE LOWER(email) = ?", (user_email,))
        user = cursor.fetchone()
        
    if not user:
        conn.close()
        return jsonify({'error': 'Profile not found'}), 404
        
    actual_user_id = user['id']
    ref_code = user['referral_code']
    if not ref_code:
        ref_code = generate_user_referral_code(cursor, actual_user_id)
        conn.commit()
        
    # 2. Fetch referrals where this student is the referrer
    cursor.execute("""
        SELECT r.*, p.full_name as referred_name, p.email as referred_email
        FROM referrals r
        JOIN profiles p ON r.referred_user_id = p.id
        WHERE r.referrer_user_id = ?
        ORDER BY r.created_at DESC
    """, (actual_user_id,))
    
    ref_rows = cursor.fetchall()
    referees = [dict(r) for r in ref_rows]
    
    total_registered = len(referees)
    total_enrolled = len([r for r in referees if r.get('status') in ('enrolled', 'rewarded')])
    
    REQUIRED_ENROLLED_TARGET = 3
    is_eligible = total_enrolled >= REQUIRED_ENROLLED_TARGET
    
    # Base Share URL
    app_base_url = Config.APP_URL.rstrip('/')
    referral_link = f"{app_base_url}/#/register?ref={ref_code}"
    
    share_msg = f"""🎓 100% FREE INTERNSHIP OPPORTUNITY FOR STUDENTS! 🚀

Hey everyone! 👋
Looking for an internship to gain real-world experience, improve your skills, and strengthen your resume? 💼🌟

Check out Web Intern! 💻✨
✨ 100% FREE Internship
📜 Get your Offer Letter instantly by email
🧠 Learn and gain practical experience
🎓 Student-friendly internship opportunities
🥇 Certificate available after completing the required eligibility/process
🚀 Quick & easy online process
⚡ No complicated application process

Join Web Intern here: 👇
{referral_link}

If you're a college student looking for an internship, definitely check it out and share it with your friends! 🌟
Start your internship journey today! 🔥💪"""
    
    whatsapp_url = f"https://api.whatsapp.com/send?text={quote(share_msg)}"
    telegram_url = f"https://t.me/share/url?url={quote(referral_link)}&text={quote(share_msg)}"
    
    conn.close()
    
    return jsonify({
        'referral_code': ref_code,
        'referral_link': referral_link,
        'share_message': share_msg,
        'whatsapp_share_url': whatsapp_url,
        'telegram_share_url': telegram_url,
        'total_registered': total_registered,
        'total_enrolled': total_enrolled,
        'target_required': REQUIRED_ENROLLED_TARGET,
        'is_eligible_for_reward': is_eligible,
        'referees': referees,
        'notice': 'Sharing alone does not grant free certificates. Rewards require referred friends to complete their internship enrollment.'
    }), 200

@referral_bp.route('/api/referrals/claim-reward', methods=['POST'])
@jwt_required
def claim_referral_reward():
    user_id = g.user_id
    user_email = (g.user_email or '').lower().strip()
    data = request.get_json() or {}
    
    certificate_id = data.get('certificate_id')
    application_id = data.get('application_id')
    
    if not certificate_id and not application_id:
        return jsonify({'error': 'certificate_id or application_id is required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify referrer profile
    cursor.execute("SELECT id FROM profiles WHERE id = ? OR LOWER(email) = ?", (user_id, user_email))
    prof = cursor.fetchone()
    if not prof:
        conn.close()
        return jsonify({'error': 'User profile not found'}), 404
        
    actual_user_id = prof['id']
    
    # Check count of active enrolled referrals
    cursor.execute("""
        SELECT id FROM referrals 
        WHERE referrer_user_id = ? AND status IN ('enrolled', 'rewarded')
    """, (actual_user_id,))
    enrolled_referrals = cursor.fetchall()
    
    if len(enrolled_referrals) < 3:
        conn.close()
        return jsonify({
            'error': f'Reward threshold not met. You have {len(enrolled_referrals)}/3 enrolled referrals. Sharing alone does not qualify.',
            'enrolled_count': len(enrolled_referrals),
            'target_required': 3
        }), 400
        
    # Unlock target certificate in local SQLite
    cursor.execute("""
        SELECT c.*, a.id as app_id FROM certificates c
        JOIN applications a ON c.application_id = a.id
        WHERE (c.id = ? OR a.certificate_id = ? OR a.id = ?)
          AND (a.user_id = ? OR LOWER(a.user_id) = ? OR a.user_id IN (SELECT id FROM profiles WHERE LOWER(email) = ?))
    """, (certificate_id or application_id, certificate_id or application_id, application_id or certificate_id, actual_user_id, user_email, user_email))
    
    cert_row = cursor.fetchone()
    if not cert_row:
        conn.close()
        return jsonify({'error': 'Enrolled certificate not found for this student'}), 404
        
    c_id = cert_row['id']
    
    cursor.execute("UPDATE certificates SET is_verified_paid = 1 WHERE id = ?", (c_id,))
    
    # Mark the 3 referrals as rewarded
    for ref in enrolled_referrals[:3]:
        cursor.execute("UPDATE referrals SET status = 'rewarded' WHERE id = ?", (ref['id'],))
        
    conn.commit()
    conn.close()
    
    log_success(f"User {user_email} claimed 100% Free Verified Certificate reward for {c_id}")
    return jsonify({
        'message': '🎉 Referral Reward Claimed Successfully! 100% Free Official Verified Certificate Unlocked.',
        'certificate_id': c_id,
        'is_verified_paid': True
    }), 200
