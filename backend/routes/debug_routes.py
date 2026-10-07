# debug_routes.py
from flask import Blueprint, jsonify
from models.database import Database

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')
db = Database()

@debug_bp.route('/check-user/<int:user_id>', methods=['GET'])
def check_user(user_id):
    """Check if user exists in database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute('SELECT id, email, name, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        # Check profiles table
        cursor.execute('SELECT * FROM student_profiles WHERE user_id = ?', (user_id,))
        profile = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user_exists': user is not None,
            'user': dict(user) if user else None,
            'profile_exists': profile is not None,
            'profile': dict(profile) if profile else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@debug_bp.route('/list-users', methods=['GET'])
def list_users():
    """List all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, name, role, profile_completed FROM users')
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@debug_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """Check if admin user exists"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, name, role FROM users WHERE role = "admin"')
        admins = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'admins': admins,
            'count': len(admins)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500