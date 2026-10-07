from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv
import pandas as pd
from werkzeug.utils import secure_filename
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object('config.Config')

# Ensure upload folder exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# In app.py, update the JWT user identity loader:

@jwt.user_identity_loader
def user_identity_lookup(user):
    print(f"JWT - Storing user identity: {user} (type: {type(user)})")
    return str(user)  # Always return string

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    print(f"JWT - Loading user with identity: {identity} (type: {type(identity)})")
    # Return the identity as is - we'll handle conversion in the routes
    return identity

# Import models
from models.database import Database
from models.ai_model import EduFundAIModel
from models.matching_engine import IntelligentMatchingEngine
from models.blockchain import ledger as blockchain

# Initialize global instances
db = Database()
ai_model = EduFundAIModel()
matching_engine = IntelligentMatchingEngine(db)

# Import all routes
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp
from routes.crowdfunding import crowdfunding_bp
from routes.work_study import work_study_bp
# Debug routes expose user records, so they are only enabled on request:
# set EDUFUND_DEBUG_ROUTES=1 in .env while developing.
if os.environ.get('EDUFUND_DEBUG_ROUTES') == '1':
    from routes.debug_routes import debug_bp
    app.register_blueprint(debug_bp)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(crowdfunding_bp)
app.register_blueprint(work_study_bp)

# Flag to track if AI model is trained
ai_model_trained = False

def train_ai_model():
    global ai_model_trained
    try:
        sample_data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_students.csv')
        if os.path.exists(sample_data_path):
            student_data = pd.read_csv(sample_data_path)
            ai_model.train(student_data)
            ai_model_trained = True
            print("✅ AI Model trained successfully!")
        else:
            print("⚠️ Sample data not found. Creating sample data...")
            os.makedirs(os.path.dirname(sample_data_path), exist_ok=True)
            
            import csv
            sample_data = [
                ['family_income', 'academic_score', 'extracurriculars', 'siblings_education', 'course_duration', 'tuition_fee', 'funding_gap', 'repayment_capacity'],
                [25000, 92, 4, 1, 4, 400000, 300000, 2],
                [45000, 78, 2, 0, 3, 350000, 250000, 1],
                [120000, 65, 1, 2, 4, 500000, 100000, 2],
                [30000, 88, 3, 2, 4, 450000, 350000, 1],
                [80000, 45, 0, 1, 3, 300000, 150000, 0],
            ]
            
            with open(sample_data_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(sample_data)
            
            student_data = pd.read_csv(sample_data_path)
            ai_model.train(student_data)
            ai_model_trained = True
            print("✅ AI Model trained with created sample data!")
    except Exception as e:
        print(f"⚠️ Could not train AI model: {e}")


# Routes
# Add this to app.py to serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

@app.route('/')
def serve_landing():
    return send_from_directory('../frontend', 'index.html')

@app.route('/student')
def serve_student():
    return send_from_directory('../frontend', 'student.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory('../frontend', 'admin.html')

@app.route('/api/blockchain/records', methods=['GET'])
def blockchain_records():
    """Blocks on the donation ledger, newest last"""
    return jsonify({
        'success': True,
        'chain_valid': blockchain.is_chain_valid(),
        'records': blockchain.get_all_transactions()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'ai_model': 'trained' if ai_model_trained else 'fallback',
        'database': 'sqlite'
    })

# Train AI model on startup
print("Starting EduFund AI...")
train_ai_model()
print(f"AI Model Status: {' Trained' if ai_model_trained else 'Using Fallback'}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)