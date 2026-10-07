# routes/ai_features.py - FIXED VERSION
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.enhanced_matching_engine import EnhancedMatchingEngine
from models.semantic_search import SemanticSearchEngine
from models.resume_analyzer import ResumeAnalyzer
from models.database import Database
import os
from werkzeug.utils import secure_filename

ai_features_bp = Blueprint('ai_features', __name__, url_prefix='/api/ai')
db = Database()
matching_engine = EnhancedMatchingEngine(db)
search_engine = SemanticSearchEngine()
resume_analyzer = ResumeAnalyzer()

# Initialize search engine with scholarships
def init_search_engine():
    """Initialize the semantic search engine with scholarships from database"""
    try:
        scholarships = db.get_scholarships({})
        if scholarships:
            search_engine.index_scholarships(scholarships)
            print(f"✅ Semantic search engine initialized with {len(scholarships)} scholarships")
        else:
            print("⚠️ No scholarships found for semantic search indexing")
    except Exception as e:
        print(f"⚠️ Error initializing semantic search: {e}")


try:
    init_search_engine()
except Exception as e:
    print(f"⚠️ Could not initialize search engine: {e}")

@ai_features_bp.route('/match/<int:opportunity_id>', methods=['GET'])
@jwt_required()
def get_enhanced_match(opportunity_id):
    """Get enhanced ML-based match score"""
    try:
        current_user_id = get_jwt_identity()
        
        # Convert to int if string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'error': 'Invalid user ID format'}), 400
        
        student_profile = db.get_student_profile(current_user_id)
        
        if not student_profile:
            return jsonify({'error': 'Complete your profile first'}), 400
        
        # Get opportunity
        opportunity_type = request.args.get('type', 'scholarship')
        if opportunity_type == 'scholarship':
            opportunities = db.get_scholarships({'id': opportunity_id})
        else:
            opportunities = db.get_work_study_opportunities({'id': opportunity_id})
        
        if not opportunities:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        opportunity = opportunities[0]
        
        
        try:
            score, explanation = matching_engine.get_enhanced_match_score(
                student_profile, opportunity, opportunity_type
            )
            
            # Predict success rate
            success_rate = matching_engine.predict_success_rate(
                student_profile, opportunity, opportunity_type
            )
        except Exception as e:
            print(f"Error in matching engine: {e}")
            # Fallback to simple match
            score = 50
            explanation = {'score': 50, 'strengths': [], 'weaknesses': [], 'suggestions': []}
            success_rate = 0.5
        
        return jsonify({
            'success': True,
            'match_score': score,
            'success_rate': success_rate,
            'explanation': explanation,
            'opportunity': opportunity
        })
        
    except Exception as e:
        print(f"Error in enhanced match: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@ai_features_bp.route('/search/scholarships', methods=['POST'])
def semantic_search():
    """Semantic search for scholarships"""
    try:
        data = request.json or {}
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        # Ensure search engine is initialized
        if search_engine.scholarship_vectors is None:
            init_search_engine()
        
        results = search_engine.search(query, top_k=data.get('top_k', 10))
        
        # Get full scholarship details
        scholarships = []
        for result in results:
            scholarship = db.get_scholarships({'id': result['scholarship_id']})
            if scholarship:
                scholarship = scholarship[0]
                scholarship['similarity_score'] = result['similarity_score']
                scholarships.append(scholarship)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': scholarships,
            'count': len(scholarships)
        })
        
    except Exception as e:
        print(f"Error in semantic search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@ai_features_bp.route('/resume/analyze', methods=['POST'])
@jwt_required()
def analyze_resume():
    """Analyze uploaded resume and extract profile information"""
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        
        temp_dir = '/tmp'
        if not os.path.exists(temp_dir):
            temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
        
        # Save temporarily
        filename = secure_filename(f"resume_{get_jwt_identity()}_{file.filename}")
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        # Analyze resume
        result = resume_analyzer.analyze_resume(filepath)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Extract profile data
        profile_data = resume_analyzer.extract_student_profile_from_resume(filepath)
        
        return jsonify({
            'success': True,
            'analysis': result,
            'suggested_profile': profile_data
        })
        
    except Exception as e:
        print(f"Error analyzing resume: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@ai_features_bp.route('/predict/success', methods=['POST'])
@jwt_required()
def predict_success():
    """Predict success rate for an application"""
    try:
        data = request.json
        current_user_id = get_jwt_identity()
        
        # Convert to int if string
        if isinstance(current_user_id, str):
            try:
                current_user_id = int(current_user_id)
            except ValueError:
                return jsonify({'error': 'Invalid user ID format'}), 400
        
        student_profile = db.get_student_profile(current_user_id)
        
        if not student_profile:
            return jsonify({'error': 'Complete your profile first'}), 400
        
        opportunity_id = data.get('opportunity_id')
        opportunity_type = data.get('type', 'scholarship')
        
        if not opportunity_id:
            return jsonify({'error': 'Opportunity ID required'}), 400
        
        # Get opportunity
        if opportunity_type == 'scholarship':
            opportunities = db.get_scholarships({'id': opportunity_id})
        else:
            opportunities = db.get_work_study_opportunities({'id': opportunity_id})
        
        if not opportunities:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        opportunity = opportunities[0]
        
        # Predict success rate
        try:
            success_rate = matching_engine.predict_success_rate(
                student_profile, opportunity, opportunity_type
            )
            
            # Get match score and explanation
            score, explanation = matching_engine.get_enhanced_match_score(
                student_profile, opportunity, opportunity_type
            )
        except Exception as e:
            print(f"Error in prediction: {e}")
            success_rate = 0.5
            score = 50
            explanation = {'score': 50, 'strengths': [], 'weaknesses': [], 'suggestions': []}
        
        # Provide recommendations
        recommendations = []
        if success_rate > 0.7:
            recommendations.append("✅ High chance of success - proceed with application")
        elif success_rate > 0.4:
            recommendations.append("📈 Moderate chance - consider strengthening your application")
        else:
            recommendations.append("⚠️ Low chance - consider other opportunities first")
        
        if explanation.get('suggestions'):
            recommendations.extend(explanation['suggestions'])
        
        return jsonify({
            'success': True,
            'success_rate': success_rate,
            'match_score': score,
            'explanation': explanation,
            'recommendations': recommendations[:5]
        })
        
    except Exception as e:
        print(f"Error predicting success: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@ai_features_bp.route('/similar/<int:scholarship_id>', methods=['GET'])
def find_similar_scholarships(scholarship_id):
    """Find scholarships similar to given one"""
    try:
        scholarships = db.get_scholarships({})
        
        
        if search_engine.scholarship_vectors is None:
            init_search_engine()
        
        results = search_engine.find_similar_scholarships(scholarship_id, scholarships)
        
        # Get full scholarship details
        similar = []
        for result in results:
            scholarship = db.get_scholarships({'id': result['scholarship_id']})
            if scholarship:
                scholarship = scholarship[0]
                scholarship['similarity_score'] = result['similarity_score']
                similar.append(scholarship)
        
        return jsonify({
            'success': True,
            'similar_scholarships': similar,
            'count': len(similar)
        })
        
    except Exception as e:
        print(f"Error finding similar scholarships: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@ai_features_bp.route('/health', methods=['GET'])
def health_check():
    """Check if AI features are working"""
    return jsonify({
        'success': True,
        'search_engine_initialized': search_engine.scholarship_vectors is not None,
        'matching_engine_trained': matching_engine.is_trained,
        'resume_analyzer_ready': True
    })