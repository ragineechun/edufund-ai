from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.database import Database

work_study_bp = Blueprint('work_study', __name__, url_prefix='/api/work-study')
db = Database()

@work_study_bp.route('/opportunities', methods=['GET'])
def get_opportunities():
    """Get all work-study opportunities"""
    try:
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
            
        opportunities = db.get_work_study_opportunities(filters)
        return jsonify({'success': True, 'opportunities': opportunities}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@work_study_bp.route('/opportunities/<int:opportunity_id>', methods=['GET'])
def get_opportunity(opportunity_id):
    """Get a specific work-study opportunity"""
    try:
        opportunities = db.get_work_study_opportunities({'id': opportunity_id})
        if opportunities:
            return jsonify({'success': True, 'opportunity': opportunities[0]}), 200
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@work_study_bp.route('/opportunities/<int:opportunity_id>/apply', methods=['POST'])
@jwt_required()
def apply_for_opportunity(opportunity_id):
    """Apply for a work-study opportunity"""
    try:
        current_user_id = get_jwt_identity()
        data = request.json
        
        application_data = {
            'student_id': current_user_id,
            'opportunity_id': opportunity_id,
            'opportunity_type': 'work_study',
            'message': data.get('message', ''),
            'documents': data.get('documents', [])
        }
        
        application_id = db.submit_application(application_data)
        
        if application_id:
            return jsonify({'success': True, 'message': 'Application submitted', 'application_id': application_id}), 201
        return jsonify({'success': False, 'error': 'Failed to submit'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500