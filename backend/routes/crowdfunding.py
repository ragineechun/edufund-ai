from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models.database import Database
from models.blockchain import ledger
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import traceback

crowdfunding_bp = Blueprint('crowdfunding', __name__, url_prefix='/api/crowdfunding')
db = Database()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


from datetime import datetime, date

@crowdfunding_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all active campaigns with proper date formatting"""
    try:
        filters = {'status': 'active'}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        campaigns = db.get_campaigns(filters)
        
        # Format dates properly
        for campaign in campaigns:
            # Handle deadline
            if campaign.get('deadline'):
                try:
                    # Check if it's a date object or string
                    if isinstance(campaign['deadline'], str):
                        # Parse the date string
                        if 'T' in campaign['deadline']:
                            deadline_date = datetime.fromisoformat(campaign['deadline'].replace('Z', '+00:00')).date()
                        else:
                            deadline_date = datetime.strptime(campaign['deadline'], '%Y-%m-%d').date()
                    elif isinstance(campaign['deadline'], date):
                        deadline_date = campaign['deadline']
                    else:
                        deadline_date = None
                    
                    if deadline_date:
                        
                        campaign['deadline'] = deadline_date.strftime('%Y-%m-%d')
                        
                        days_left = (deadline_date - datetime.now().date()).days
                        campaign['days_left'] = max(0, days_left)
                    else:
                        campaign['deadline'] = None
                        campaign['days_left'] = None
                except Exception as e:
                    print(f"Error formatting deadline: {e}")
                    campaign['deadline'] = None
                    campaign['days_left'] = None
            else:
                campaign['deadline'] = None
                campaign['days_left'] = None
            
            # Add image URL
            if campaign.get('image_path'):
                campaign['image_url'] = f"/{campaign['image_path']}"
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        print(f"Error getting campaigns: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@crowdfunding_bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    """Create a new crowdfunding campaign"""
    try:
        current_user_id = get_jwt_identity()
        user = db.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        
        title = None
        description = ""
        story = ""
        goal_amount = None
        category = "education"
        deadline = None
        image_path = None
        
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            
            title = request.form.get('title')
            description = request.form.get('description', '')
            story = request.form.get('story', '')
            goal_amount = request.form.get('goal_amount')
            category = request.form.get('category', 'education')
            deadline = request.form.get('deadline')
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Create uploads directory 
                    upload_dir = os.path.join(current_app.root_path, 'uploads', 'campaigns')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate unique filename
                    import uuid
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                    filename = f"campaign_{current_user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                    filepath = os.path.join('uploads', 'campaigns', filename)
                    full_path = os.path.join(current_app.root_path, filepath)
                    
                    # Save file
                    file.save(full_path)
                    image_path = filepath
                    print(f"✅ Image saved: {full_path}")
                    print(f"✅ Image path: {image_path}")
        else:
            # Handle JSON data
            data = request.get_json() or {}
            title = data.get('title')
            description = data.get('description', '')
            story = data.get('story', '')
            goal_amount = data.get('goal_amount')
            category = data.get('category', 'education')
            deadline = data.get('deadline')
        
        # Validate required fields
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        if not goal_amount:
            return jsonify({'success': False, 'error': 'Goal amount is required'}), 400
        
        # Convert goal_amount to float
        try:
            goal_amount = float(goal_amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Goal amount must be a number'}), 400
        
        # Create campaign data
        campaign_data = {
            'student_id': current_user_id,
            'student_name': user.get('name', 'Unknown'),
            'title': title,
            'description': description,
            'story': story,
            'goal_amount': goal_amount,
            'deadline': deadline,
            'category': category
        }
        
        # Create campaign in database
        campaign_id = db.create_campaign(campaign_data, image_path)
        
        if campaign_id:
            return jsonify({
                'success': True,
                'message': 'Campaign created successfully',
                'campaign_id': campaign_id,
                'image_path': image_path,
                'image_url': f"/{image_path}" if image_path else None
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create campaign'}), 500
        
    except Exception as e:
        print(f"Error creating campaign: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@crowdfunding_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get specific campaign details"""
    try:
        campaign = db.get_campaign(campaign_id)
        
        if campaign:
            if campaign.get('image_path'):
                campaign['image_url'] = f"/{campaign['image_path']}"
            return jsonify({'success': True, 'campaign': campaign})
        else:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
            
    except Exception as e:
        print(f"Error getting campaign: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@crowdfunding_bp.route('/campaigns/<int:campaign_id>/donate', methods=['POST'])
@jwt_required()
def donate_to_campaign(campaign_id):
    """Process a donation"""
    try:
        data = request.json
        
        if not data or 'amount' not in data:
            return jsonify({'success': False, 'error': 'Amount is required'}), 400
        
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Amount must be a valid number'}), 400
        
        
        current_user_id = get_jwt_identity()
        donor_name = data.get('name', 'Anonymous')
        donor_email = data.get('email')
        
        
        if current_user_id:
            user = db.get_user_by_id(current_user_id)
            if user:
                if donor_name == 'Anonymous' or not data.get('name'):
                    donor_name = user.get('name', 'Anonymous')
                if not donor_email:
                    donor_email = user.get('email')
        
        donor_data = {
            'name': donor_name,
            'email': donor_email,
            'amount': amount,
            'message': data.get('message', ''),
            'anonymous': data.get('anonymous', False)
        }
        
        success = db.donate_to_campaign(campaign_id, donor_data)
        
        if success:
            
            campaign = db.get_campaign(campaign_id)
            # Record the donation on the ledger (no email is stored there)
            blockchain_tx = ledger.create_transaction({
                'type': 'donation',
                'campaign_id': campaign_id,
                'amount': amount,
                'donor': 'Anonymous' if donor_data['anonymous'] else donor_name
            })
            return jsonify({
                'success': True,
                'message': 'Thank you for your donation!',
                'blockchain_tx': blockchain_tx,
                'campaign': campaign
            })
        else:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
            
    except Exception as e:
        print(f"Error processing donation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@crowdfunding_bp.route('/campaigns/user/my', methods=['GET'])
@jwt_required()
def get_my_campaigns():
    """Get current user's campaigns"""
    try:
        current_user_id = get_jwt_identity()
        
        campaigns = db.get_campaigns({'student_id': current_user_id})
        
        for campaign in campaigns:
            if campaign.get('image_path'):
                campaign['image_url'] = f"/{campaign['image_path']}"
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        print(f"Error getting user campaigns: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@crowdfunding_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'success': True, 'message': 'Crowdfunding API is working'})