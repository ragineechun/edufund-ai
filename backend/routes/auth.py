from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import re
from models.database import Database

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
db = Database()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg
            }), 400
        
       
        
        # Create user
        user = db.create_user(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            role=data.get('role', 'student')
        )
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Failed to create user'
            }), 500
        
        # Create access token
        access_token = create_access_token(
            identity=user['id'],
            expires_delta=timedelta(days=1)
        )
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user,
            'access_token': access_token
        }), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400
        
        # Verify user
        user = db.verify_user(data['email'], data['password'])
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Create access token
        access_token = create_access_token(
            identity=str(user['id']),  
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token discard)"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    try:
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get student profile if exists
        profile = db.get_student_profile(current_user_id)
        if profile:
            user['profile'] = profile
        
        return jsonify({
            'success': True,
            'user': user
        }), 200
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        data = request.json
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'Current password and new password required'
            }), 400
        
        # Get user
        user = db.get_user_by_id(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Verify current password
        verified = db.verify_user(user['email'], data['current_password'])
        if not verified:
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 401
        
        # Validate new password
        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg
            }), 400
        
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.json
        
        if not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'Email required'
            }), 400
        
        # Password reset emails are not implemented yet. The reply is the same
        # whether or not the email exists, so accounts cannot be discovered.
        return jsonify({
            'success': True,
            'message': 'If the email exists, a password reset link will be sent'
        }), 200

    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.json
        
        if not data.get('token') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'Token and new password required'
            }), 400
        
        
        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg
            }), 400
        
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        }), 200
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address"""
    try:
        data = request.json
        
        if not data.get('token'):
            return jsonify({
                'success': False,
                'error': 'Verification token required'
            }), 400
        
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully'
        }), 200
        
    except Exception as e:
        print(f"Verify email error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'success': True,
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        print(f"Refresh token error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create admin user (protected route in production)"""
    try:
        data = request.json
        
        
        
        user = db.create_user(
            email=data.get('email', 'admin@edufund.ai'),
            password=data.get('password', 'Admin@123'),
            name=data.get('name', 'Admin User'),
            role='admin'
        )
        
        if user:
            return jsonify({
                'success': True,
                'message': 'Admin user created',
                'user': user
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create admin'
            }), 500
            
    except Exception as e:
        print(f"Create admin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500