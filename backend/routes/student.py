from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.database import Database
import traceback

student_bp = Blueprint('student', __name__, url_prefix='/api/student')
db = Database()

@student_bp.route('/profile', methods=['POST', 'OPTIONS'])
@jwt_required()
def complete_profile():
    """Complete student profile"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Get user ID from JWT - this might be a string
        current_user_id = get_jwt_identity()
        print(f"JWT Identity: {current_user_id} (type: {type(current_user_id)})")
        
        # Convert to int if it's a string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
                print(f"Converted to int: {current_user_id}")
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid user ID format'}), 400
        
        data = request.json
        print(f"Received profile data for user {current_user_id}: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['academic_score', 'family_income', 'course', 'institution', 'tuition_fee']
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            print(f"Validation error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Convert values with error handling
        try:
            profile_data = {
                'academic_score': float(data.get('academic_score', 0)),
                'family_income': float(data.get('family_income', 0)),
                'extracurriculars': int(data.get('extracurriculars', 0)),
                'siblings_education': int(data.get('siblings_education', 0)),
                'course': str(data.get('course', '')),
                'institution': str(data.get('institution', '')),
                'course_duration': int(data.get('course_duration', 4)),
                'tuition_fee': float(data.get('tuition_fee', 0)),
                'skills': data.get('skills', []),
                'preferred_location': data.get('preferred_location'),
                'preferred_hours': data.get('preferred_hours'),
                'expected_stipend': data.get('expected_stipend')
            }
            print(f"Processed profile data: {profile_data}")
        except ValueError as e:
            print(f"Value conversion error: {e}")
            return jsonify({'success': False, 'error': f'Invalid number format: {str(e)}'}), 400
        
        # Create profile in database
        print(f"Creating profile for user_id: {current_user_id} (type: {type(current_user_id)})")
        profile = db.create_student_profile(current_user_id, profile_data)
        print(f"Database result: {profile}")
        
        if profile:
            return jsonify({
                'success': True,
                'message': 'Profile completed successfully',
                'profile': profile
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to create profile in database'}), 500
        
    except Exception as e:
        print(f"Error in complete_profile: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

  
@student_bp.route('/<int:student_id>/assess', methods=['POST'])
@jwt_required()
def assess_student(student_id):
    """Run AI assessment for student"""
    try:
        from models.ai_model import EduFundAIModel
        ai_model = EduFundAIModel()
        
        data = request.json
        
        # Get AI assessment
        assessment = ai_model.predict_funding_needs({
            'family_income': float(data.get('familyIncome', data.get('family_income', 0))),
            'academic_score': float(data.get('academicScore', data.get('academic_score', 0))),
            'extracurriculars': int(data.get('extracurriculars', 0)),
            'siblings_education': int(data.get('siblingsEducation', data.get('siblings_education', 0))),
            'course_duration': int(data.get('courseDuration', data.get('course_duration', 4))),
            'tuition_fee': float(data.get('tuitionFee', data.get('tuition_fee', 0)))
        })
        
        # Get recommendations
        recommendations = ai_model.recommend_funding(data, assessment)
        
        return jsonify({
            'success': True,
            'assessment': assessment,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Error in assess_student: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/<int:student_id>/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations(student_id):
    """Get personalized recommendations for student"""
    try:
        from models.matching_engine import IntelligentMatchingEngine
        engine = IntelligentMatchingEngine(db)
        
        recommendations = engine.get_personalized_recommendations(student_id)
        
        
        for rec in recommendations:
            if rec['type'] == 'scholarship' and 'link' not in rec:
                rec['link'] = '#'  
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/<int:student_id>/apply', methods=['POST'])
@jwt_required()
def apply_for_opportunity(student_id):
    """Apply for a scholarship or work-study"""
    try:
        current_user_id = get_jwt_identity()
        
        
        if str(current_user_id) != str(student_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        
        application = {
            'student_id': student_id,
            'opportunity_id': data['opportunity_id'],
            'opportunity_type': data['type'],  
            'message': data.get('message', ''),
            'documents': data.get('documents', [])
        }
        
        application_id = db.submit_application(application)
        
        if application_id:
            return jsonify({
                'success': True,
                'message': 'Application submitted',
                'application_id': application_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to submit application'}), 500
        
    except Exception as e:
        print(f"Error in apply_for_opportunity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/<int:student_id>/applications', methods=['GET'])
@jwt_required()
def get_applications(student_id):
    """Get student's applications"""
    try:
        current_user_id = get_jwt_identity()
        
        
        if str(current_user_id) != str(student_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        applications = db.get_student_applications(student_id)
        
        return jsonify({
            'success': True,
            'applications': applications
        })
        
    except Exception as e:
        print(f"Error in get_applications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@student_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_personalized_recommendations():
    """Get personalized recommendations from database"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get student profile
        profile = db.get_student_profile(current_user_id)
        if not profile:
            return jsonify({'success': False, 'error': 'Complete your profile first'}), 400
        
        # Get all active scholarships
        scholarships = db.get_scholarships({'status': 'active'})
        
        # Get all open work-study opportunities
        work_study = db.get_work_study_opportunities({'status': 'open'})
        
        recommendations = []
        
        # Match scholarships
        for s in scholarships:
            score = 0
            reasons = []
            
            # Academic score match
            if s.get('min_academic_score') and profile.get('academic_score', 0) >= s['min_academic_score']:
                score += 30
                reasons.append(f"Meets minimum score of {s['min_academic_score']}%")
            
            # Income match
            if s.get('max_income') and profile.get('family_income', 0) <= s['max_income']:
                score += 25
                reasons.append(f"Income within limit (₹{s['max_income']})")
            
            # Course match
            eligible_courses = s.get('eligible_courses', [])
            if eligible_courses and ('all' in [c.lower() for c in eligible_courses] or 
                                     profile.get('course', '').lower() in [c.lower() for c in eligible_courses]):
                score += 20
                reasons.append("Course matches eligibility")
            
            if score > 50:  # Only include good matches
                recommendations.append({
                    'id': s['id'],
                    'name': s['name'],
                    'provider': s['provider'],
                    'amount': s['amount'],
                    'type': 'scholarship',
                    'match_score': score,
                    'reasons': reasons,
                    'deadline': s.get('deadline'),
                    'link': s.get('link', '#')  # Include link
                })
        
        # Match work-study (no changes needed here)
        for w in work_study:
            score = 0
            reasons = []
            
            # Skills match
            required_skills = w.get('required_skills', [])
            student_skills = profile.get('skills', [])
            matching_skills = set(student_skills) & set(required_skills)
            if matching_skills:
                score += min(30, len(matching_skills) * 10)
                reasons.append(f"Skills match: {', '.join(list(matching_skills)[:2])}")
            
            # Hours match
            pref_hours = profile.get('preferred_hours')
            if pref_hours and abs(w['hours_per_week'] - pref_hours) <= 5:
                score += 20
                reasons.append(f"Hours match ({w['hours_per_week']}/week)")
            
            # Location match
            if w.get('remote'):
                score += 15
                reasons.append("Remote work available")
            
            if score > 40:
                recommendations.append({
                    'id': w['id'],
                    'title': w['title'],
                    'organization': w['organization'],
                    'stipend': w['stipend'],
                    'hours_per_week': w['hours_per_week'],
                    'type': 'work_study',
                    'match_score': score,
                    'reasons': reasons,
                    'remote': w.get('remote', False),
                    'location': w.get('location')
                })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations[:10]  # Top 10
        })
        
    except Exception as e:
        print(f"Error in recommendations: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@student_bp.route('/scholarships/all', methods=['GET'])
@jwt_required()
def get_all_scholarships():
    """Get all scholarships for browsing"""
    try:
        # Get all scholarships from database
        scholarships = db.get_scholarships({})
        
        # Format the scholarships for display
        formatted_scholarships = []
        for s in scholarships:
            formatted_scholarships.append({
                'id': s['id'],
                'name': s['name'],
                'provider': s['provider'],
                'description': s.get('description', ''),
                'amount': s['amount'],
                'deadline': s.get('deadline'),
                'link': s.get('link', '#'),  
                'min_academic_score': s.get('min_academic_score'),
                'max_income': s.get('max_income'),
                'eligible_courses': s.get('eligible_courses', []),
                'merit_based': bool(s.get('merit_based', False)),
                'need_based': bool(s.get('need_based', False)),
                'requires_extracurricular': bool(s.get('requires_extracurricular', False)),
                'status': s.get('status', 'active'),
                'applications_received': s.get('applications_received', 0)
            })
        
        return jsonify({
            'success': True,
            'scholarships': formatted_scholarships
        })
        
    except Exception as e:
        print(f"Error getting all scholarships: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/scholarships/active', methods=['GET'])
@jwt_required()
def get_active_scholarships():
    """Get only active scholarships"""
    try:
        scholarships = db.get_scholarships({'status': 'active'})
        return jsonify({
            'success': True,
            'scholarships': scholarships
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@student_bp.route('/scholarships/<int:scholarship_id>/check-eligibility', methods=['GET'])
@jwt_required()
def check_scholarship_eligibility(scholarship_id):
    """Check if current student is eligible for a specific scholarship"""
    try:
        current_user_id = get_jwt_identity()
        profile = db.get_student_profile(current_user_id)
        scholarship = db.get_scholarships({'id': scholarship_id})
        
        if not scholarship:
            return jsonify({'success': False, 'error': 'Scholarship not found'}), 404
        
        scholarship = scholarship[0]
        eligibility = {
            'eligible': True,
            'criteria': []
        }
        
        # Check each criterion
        if scholarship.get('min_academic_score'):
            meets = profile.get('academic_score', 0) >= scholarship['min_academic_score']
            eligibility['criteria'].append({
                'name': f"Minimum academic score of {scholarship['min_academic_score']}%",
                'met': meets,
                'value': profile.get('academic_score')
            })
            if not meets:
                eligibility['eligible'] = False
        
        if scholarship.get('max_income'):
            meets = profile.get('family_income', 0) <= scholarship['max_income']
            eligibility['criteria'].append({
                'name': f"Maximum income of ₹{scholarship['max_income']}",
                'met': meets,
                'value': profile.get('family_income')
            })
            if not meets:
                eligibility['eligible'] = False
        
        return jsonify({
            'success': True,
            'eligibility': eligibility
        })
        
    except Exception as e:
        print(f"Error checking eligibility: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500