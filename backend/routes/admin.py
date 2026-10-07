from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models.database import Database
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
import traceback

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
db = Database()

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login using the auth system"""
    try:
        data = request.json
        
        # Use the same auth logic as regular login
        user = db.verify_user(data.get('email'), data.get('password'))
        
        if user and user.get('role') == 'admin':
            # Make sure user ID is a string for JWT
            access_token = create_access_token(identity=str(user['id']))
            
            return jsonify({
                'success': True,
                'token': access_token,
                'user': user
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Invalid credentials or not an admin'
            }), 401
            
    except Exception as e:
        print(f"Admin login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# admin.py - Fix add_scholarship endpoint
@admin_bp.route('/scholarships', methods=['POST'])
@jwt_required()
def add_scholarship():
    """Add a new scholarship"""
    try:
        # Get user ID from JWT
        current_user_id = get_jwt_identity()
        print(f"Adding scholarship - User ID: {current_user_id}")
        
        # Convert to int if string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
        
        # Verify admin role
        user = db.get_user_by_id(current_user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        if user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Admin access required'}), 403
        
        data = request.json
        print(f"Received scholarship data: {data}")
        
        # Validate required fields
        required = ['name', 'provider', 'amount', 'deadline', 'link']
        missing_fields = []
        for field in required:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Amount must be a valid number'}), 400
        
        # Process eligible courses
        eligible_courses = data.get('eligible_courses', [])
        if isinstance(eligible_courses, str):
            eligible_courses = [c.strip() for c in eligible_courses.split(',') if c.strip()]
        
        # Prepare scholarship data
        scholarship_data = {
            'name': data['name'].strip(),
            'provider': data['provider'].strip(),
            'description': data.get('description', '').strip(),
            'amount': amount,
            'deadline': data['deadline'],
            'link': data['link'].strip(),
            'min_academic_score': data.get('min_academic_score'),
            'max_income': data.get('max_income'),
            'eligible_courses': eligible_courses,
            'merit_based': bool(data.get('merit_based', False)),
            'need_based': bool(data.get('need_based', False)),
            'requires_extracurricular': bool(data.get('requires_extracurricular', False)),
            'other_requirements': data.get('other_requirements', '').strip(),
            'total_slots': data.get('total_slots')
        }
        
        print(f"Processed scholarship data: {scholarship_data}")
        
        # Add to database
        scholarship_id = db.add_scholarship(scholarship_data)
        
        if scholarship_id:
            return jsonify({
                'success': True,
                'message': 'Scholarship added successfully',
                'scholarship_id': scholarship_id
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to add scholarship to database'}), 500
        
    except Exception as e:
        print(f"Error adding scholarship: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@admin_bp.route('/scholarships/<int:scholarship_id>', methods=['DELETE'])
@jwt_required()
def delete_scholarship(scholarship_id):
    """Delete a scholarship"""
    try:
        # Verify admin role
        current_user_id = get_jwt_identity()
        # Convert to int if string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
                
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete from database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scholarships WHERE id = ?", (scholarship_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Scholarship deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Scholarship not found'}), 404
            
    except Exception as e:
        print(f"Error deleting scholarship: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    


@admin_bp.route('/scholarships', methods=['GET'])
@jwt_required()
def get_all_scholarships():
    """Get all scholarships (admin view)"""
    try:
        # Verify admin role
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        scholarships = db.get_scholarships({})
        
        return jsonify({
            'success': True,
            'scholarships': scholarships
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/scholarships/<int:scholarship_id>', methods=['PUT'])
@jwt_required()
def update_scholarship(scholarship_id):
    """Update scholarship details"""
    try:
        # Verify admin role
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        
        # Prepare update data
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'provider' in data:
            update_data['provider'] = data['provider']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'amount' in data:
            update_data['amount'] = float(data['amount'])
        if 'deadline' in data:
            update_data['deadline'] = data['deadline']
        if 'status' in data:
            update_data['status'] = data['status']
        if 'min_academic_score' in data:
            update_data['min_academic_score'] = data['min_academic_score']
        if 'max_income' in data:
            update_data['max_income'] = data['max_income']
        if 'eligible_courses' in data:
            update_data['eligible_courses'] = data['eligible_courses']
        if 'merit_based' in data:
            update_data['merit_based'] = data['merit_based']
        if 'need_based' in data:
            update_data['need_based'] = data['need_based']
        
        success = db.update_scholarship(scholarship_id, update_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Scholarship updated'})
        else:
            return jsonify({'success': False, 'error': 'Scholarship not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/scholarships/<int:scholarship_id>/students', methods=['GET'])
@jwt_required()
def get_eligible_students(scholarship_id):
    """Find eligible students for a scholarship"""
    try:
        # Verify admin role
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        from models.matching_engine import IntelligentMatchingEngine
        engine = IntelligentMatchingEngine(db)
        
        eligible_students = engine.find_students_for_scholarship(scholarship_id)
        
        return jsonify({
            'success': True,
            'eligible_students': eligible_students[:20]  # Top 20
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/work-study', methods=['POST'])
@jwt_required()
def add_work_study():
    """Add work-study opportunity"""
    try:
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        
        # Validate required fields
        required = ['title', 'organization', 'stipend', 'hours_per_week']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        work_study_data = {
            'title': data['title'],
            'organization': data['organization'],
            'description': data.get('description', ''),
            'stipend': float(data['stipend']),
            'hours_per_week': int(data['hours_per_week']),
            'duration_months': int(data.get('duration_months', 6)),
            'location': data.get('location', ''),
            'remote': data.get('remote', False),
            'required_skills': data.get('required_skills', []),
            'deadline': data.get('deadline'),
            'positions_available': int(data.get('positions_available', 1))
        }
        
        work_study_id = db.add_work_study(work_study_data)
        
        if work_study_id:
            return jsonify({
                'success': True,
                'message': 'Work-study opportunity added',
                'work_study_id': work_study_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add work-study'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/work-study', methods=['GET'])
@jwt_required()
def get_all_work_study():
    """Get all work-study opportunities"""
    try:
        # Verify admin role
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        opportunities = db.get_work_study_opportunities({})
        
        return jsonify({
            'success': True,
            'opportunities': opportunities
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        current_user_id = get_jwt_identity()
        print(f"Dashboard - current_user_id: {current_user_id} (type: {type(current_user_id)})")
        
        # Convert to int if it's a string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid user ID format'}), 400
        
        # Verify admin role
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get stats from database
        stats = db.get_admin_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_applications': stats.get('recent_applications', [])
        })
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        

# admin.py - Update get_all_students with debug prints
@admin_bp.route('/students', methods=['GET'])
@jwt_required()
def get_all_students():
    """Get all students with their profiles"""
    try:
        current_user_id = get_jwt_identity()
        
        # Convert to int if string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
        
        # Verify admin role
        user = db.get_user_by_id(current_user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get all students with their profiles
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Query to get all students with their profile data
        cursor.execute('''
            SELECT 
                u.id,
                u.email,
                u.name,
                u.role,
                u.profile_completed,
                u.created_at,
                sp.academic_score,
                sp.family_income,
                sp.extracurriculars,
                sp.siblings_education,
                sp.course,
                sp.institution,
                sp.course_duration,
                sp.tuition_fee,
                sp.skills,
                sp.preferred_location,
                sp.preferred_hours,
                sp.expected_stipend
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE u.role = 'student'
            ORDER BY u.created_at DESC
        ''')
        
        students = []
        for row in cursor.fetchall():
            student = dict(row)
            # Parse skills if present
            if student.get('skills'):
                try:
                    import json
                    student['skills'] = json.loads(student['skills'])
                except:
                    student['skills'] = []
            else:
                student['skills'] = []
            students.append(student)
        
        conn.close()
        
        print(f"Found {len(students)} students")  # Debug print
        
        return jsonify({
            'success': True,
            'students': students
        })
        
    except Exception as e:
        print(f"Error getting students: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/setup', methods=['POST'])
def setup_admin():
    """Create initial admin user (run once)"""
    try:
        # Check if admin exists
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            return jsonify({
                'success': False, 
                'error': 'Admin already exists'
            }), 400
        
        # Create admin user
        user = db.create_user(
            email='admin@edufund.ai',
            password='admin123',
            name='Admin User',
            role='admin'
        )
        
        if user:
            return jsonify({
                'success': True,
                'message': 'Admin user created successfully',
                'user': user
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create admin'
            }), 500
            
    except Exception as e:
        print(f"Setup admin error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    """Create initial admin user (run once)"""
    try:
        # Check if admin exists
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            return jsonify({
                'success': False, 
                'error': 'Admin already exists'
            }), 400
        
        # Create admin user
        user = db.create_user(
            email='admin@edufund.ai',
            password='admin123',
            name='Admin User',
            role='admin'
        )
        
        if user:
            return jsonify({
                'success': True,
                'message': 'Admin user created successfully',
                'user': user
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create admin'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500