import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

class EduFundAIModel:
    def __init__(self):
        self.funding_gap_model = None
        self.repayment_capacity_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train(self, data):
        """Train AI models on student data"""
        
        # Prepare features
        features = ['family_income', 'academic_score', 'extracurriculars', 
                   'siblings_education', 'course_duration', 'tuition_fee']
        
        X = data[features].values
        
        # Target 1: Funding gap (tuition_fee - what they can afford)
        if 'funding_gap' in data.columns:
            y_gap = data['funding_gap'].values
        else:
            # Calculate funding gap (assuming 30% of income can go to education)
            y_gap = data['tuition_fee'] - (data['family_income'] * 0.3 * data['course_duration'])
            y_gap = np.maximum(0, y_gap)  # No negative funding gap
        
        # Target 2: Repayment capacity (0 = low, 1 = medium, 2 = high)
        if 'repayment_capacity' in data.columns:
            y_repay = data['repayment_capacity'].values
        else:
            # Calculate based on family income and academics
            capacity = np.where(
                (data['family_income'] > 100000) & (data['academic_score'] > 80), 2,
                np.where((data['family_income'] > 50000) | (data['academic_score'] > 70), 1, 0)
            )
            y_repay = capacity
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_gap_train, y_gap_test = train_test_split(
            X_scaled, y_gap, test_size=0.2, random_state=42
        )
        _, _, y_repay_train, y_repay_test = train_test_split(
            X_scaled, y_repay, test_size=0.2, random_state=42
        )
        
        # Train models
        self.funding_gap_model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=10, 
            random_state=42,
            n_jobs=-1
        )
        self.funding_gap_model.fit(X_train, y_gap_train)
        
        self.repayment_capacity_model = RandomForestClassifier(
            n_estimators=100, 
            max_depth=10, 
            random_state=42,
            n_jobs=-1
        )
        self.repayment_capacity_model.fit(X_train, y_repay_train)
        
        # Calculate accuracy
        gap_score = self.funding_gap_model.score(X_test, y_gap_test)
        repay_score = self.repayment_capacity_model.score(X_test, y_repay_test)
        
        self.is_trained = True
        print(f" Models trained! Funding gap R²: {gap_score:.2f}, Repayment accuracy: {repay_score:.2f}")
        
    def predict_funding_needs(self, student_features):
        """Predict funding needs for a student"""
        
        if not self.is_trained:
            # Fallback rule-based system if model not trained
            return self._rule_based_assessment(student_features)
        
        try:
            # Prepare features
            features = np.array([[
                float(student_features['family_income']),
                float(student_features['academic_score']),
                int(student_features['extracurriculars']),
                int(student_features['siblings_education']),
                int(student_features['course_duration']),
                float(student_features['tuition_fee'])
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict funding gap
            funding_gap = self.funding_gap_model.predict(features_scaled)[0]
            
            # Predict repayment capacity
            capacity_probs = self.repayment_capacity_model.predict_proba(features_scaled)[0]
            capacity_labels = ['Low', 'Medium', 'High']
            repayment_capacity = capacity_labels[np.argmax(capacity_probs)]
            
            # Calculate eligibility score (0-100)
            eligibility_score = min(100, (
                (float(student_features['academic_score']) * 0.4) +
                (100 - min(100, float(student_features['family_income']) / 2000)) * 0.3 +
                (int(student_features['extracurriculars']) * 10) * 0.3
            ))
            
            # Calculate risk level
            risk_map = {'High': 'Low', 'Medium': 'Medium', 'Low': 'High'}
            risk_level = risk_map[repayment_capacity]
            
            return {
                'funding_gap': round(max(0, funding_gap), 2),
                'repayment_capacity': repayment_capacity,
                'eligibility_score': round(eligibility_score, 2),
                'risk_level': risk_level
            }
            
        except Exception as e:
            print(f"Error in AI prediction: {e}")
            return self._rule_based_assessment(student_features)
    
    def _rule_based_assessment(self, features):
        """Fallback rule-based assessment"""
        try:
            income = float(features['family_income'])
            score = float(features['academic_score'])
            tuition = float(features['tuition_fee'])
            duration = int(features['course_duration'])
            extracurriculars = int(features.get('extracurriculars', 0))
            
            # Calculate funding gap
            affordable = income * 0.3 * duration
            funding_gap = max(0, tuition - affordable)
            
            # Determine repayment capacity
            if income > 100000 and score > 80:
                capacity = 'High'
            elif income > 50000 or score > 70:
                capacity = 'Medium'
            else:
                capacity = 'Low'
            
            # Eligibility score
            eligibility = min(100, (score * 0.5) + (50 - min(50, income/2000)) * 0.5 + (extracurriculars * 5))
            
            risk_map = {'High': 'Low', 'Medium': 'Medium', 'Low': 'High'}
            
            return {
                'funding_gap': round(funding_gap, 2),
                'repayment_capacity': capacity,
                'eligibility_score': round(eligibility, 2),
                'risk_level': risk_map[capacity]
            }
        except Exception as e:
            print(f"Error in rule-based assessment: {e}")
            return {
                'funding_gap': 100000,
                'repayment_capacity': 'Medium',
                'eligibility_score': 50,
                'risk_level': 'Medium'
            }
    
    def recommend_funding(self, features, assessment):
        """Generate funding recommendations based on assessment"""
        recommendations = []
        
        try:
            funding_gap = assessment['funding_gap']
            capacity = assessment['repayment_capacity']
            score = float(features['academic_score'])
            
            # Scholarship recommendation
            if score > 75:
                scholarship_amount = min(funding_gap * 0.4, 200000)
                recommendations.append({
                    'type': 'Merit Scholarship',
                    'amount': round(scholarship_amount, 2),
                    'description': 'Based on your excellent academic performance',
                    'eligibility': 'High' if score > 85 else 'Medium',
                    'icon': 'fa-star'
                })
            
            # Income-based loan recommendation
            if capacity != 'Low':
                loan_amount = funding_gap * (0.8 if capacity == 'High' else 0.6)
                recommendations.append({
                    'type': 'Income-Contingent Loan',
                    'amount': round(loan_amount, 2),
                    'description': 'Repayment starts after employment, based on income',
                    'interest_rate': '8%',
                    'eligibility': capacity,
                    'icon': 'fa-hand-holding-usd'
                })
            
            # Work-study recommendation
            work_study_amount = min(funding_gap * 0.3, 100000)
            recommendations.append({
                'type': 'Work-Study Program',
                'amount': round(work_study_amount, 2),
                'description': 'Earn while you learn - part-time work on campus',
                'hours_per_week': '15-20',
                'eligibility': 'Medium',
                'icon': 'fa-briefcase'
            })
            
            # Crowdfunding recommendation
            if funding_gap > 0:
                recommendations.append({
                    'type': 'Community Crowdfunding',
                    'amount': round(funding_gap * 0.2, 2),
                    'description': 'Raise funds from alumni and community',
                    'platform': 'EduFund AI Community',
                    'eligibility': 'Open to all',
                    'icon': 'fa-users'
                })
            
            # Employer sponsorship for high achievers
            if score > 80 and capacity == 'High':
                recommendations.append({
                    'type': 'Employer Sponsorship',
                    'amount': round(funding_gap * 0.5, 2),
                    'description': 'Corporate sponsorship with internship commitment',
                    'partner_companies': ['TechCorp', 'EduFund Partners', 'Future Leaders Program'],
                    'eligibility': 'High',
                    'icon': 'fa-building'
                })
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
        
        return recommendations[:4]  # Return top 4 recommendations