# models/enhanced_matching_engine.py
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
import json
from collections import Counter

class EnhancedMatchingEngine:
    def __init__(self, db):
        self.db = db
        self.scaler = StandardScaler()
        self.success_model = None
        self.scholarship_model = None
        self.work_study_model = None
        self.is_trained = False
        self.model_path = 'models/trained/'
        
        # Create directory if not exists
        os.makedirs(self.model_path, exist_ok=True)
        
        # Load or train models
        self.load_or_train_models()
        
    def load_or_train_models(self):
        """Load pre-trained models or create new ones"""
        try:
            # Try to load existing models
            self.success_model = joblib.load(os.path.join(self.model_path, 'success_model.pkl'))
            self.scholarship_model = joblib.load(os.path.join(self.model_path, 'scholarship_model.pkl'))
            self.work_study_model = joblib.load(os.path.join(self.model_path, 'work_study_model.pkl'))
            self.is_trained = True
            print("✅ Loaded pre-trained ML models")
        except:
            # Create fallback rule-based models
            print("⚠️ Training new ML models with synthetic data...")
            self._train_fallback_models()
    
    def _train_fallback_models(self):
        """Create trained models using synthetic data"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Features: academic_score, family_income, extracurriculars, skills_count, tuition_fee
        X = np.random.rand(n_samples, 5)
        X[:, 0] = X[:, 0] * 100  # academic_score 0-100
        X[:, 1] = X[:, 1] * 500000  # family_income 0-500k
        X[:, 2] = X[:, 2] * 10  # extracurriculars 0-10
        X[:, 3] = X[:, 3] * 15  # skills_count 0-15
        X[:, 4] = X[:, 4] * 400000  # tuition_fee 0-400k
        
        # Success probability (based on rules)
        success_probs = (X[:, 0] / 100) * 0.5 + (1 - X[:, 1] / 500000) * 0.3 + (X[:, 2] / 10) * 0.2
        success_probs = np.clip(success_probs + np.random.normal(0, 0.1, n_samples), 0, 1)
        
        # Scholarship eligibility score (0-100)
        scholarship_scores = (X[:, 0] / 100) * 40 + (1 - X[:, 1] / 500000) * 30 + (X[:, 2] / 10) * 20 + (X[:, 3] / 15) * 10
        scholarship_scores = np.clip(scholarship_scores + np.random.normal(0, 10, n_samples), 0, 100)
        
        # Work-study match score (0-100)
        work_study_scores = (1 - X[:, 1] / 500000) * 30 + (X[:, 3] / 15) * 40 + (X[:, 2] / 10) * 30
        work_study_scores = np.clip(work_study_scores + np.random.normal(0, 10, n_samples), 0, 100)
        
        # Train models
        self.success_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scholarship_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.work_study_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        self.success_model.fit(X, success_probs)
        self.scholarship_model.fit(X, scholarship_scores)
        self.work_study_model.fit(X, work_study_scores)
        
        self.is_trained = True
        
        # Save models
        joblib.dump(self.success_model, os.path.join(self.model_path, 'success_model.pkl'))
        joblib.dump(self.scholarship_model, os.path.join(self.model_path, 'scholarship_model.pkl'))
        joblib.dump(self.work_study_model, os.path.join(self.model_path, 'work_study_model.pkl'))
        
        print("✅ Trained and saved ML models")
    
    def _extract_features_for_matching(self, student_profile: Dict, opportunity: Dict, 
                                       opp_type: str) -> np.ndarray:
        """Extract features for ML prediction"""
        # Calculate base features
        academic_score = student_profile.get('academic_score', 0)
        family_income = student_profile.get('family_income', 0)
        extracurriculars = student_profile.get('extracurriculars', 0)
        skills_count = len(student_profile.get('skills', []))
        tuition_fee = student_profile.get('tuition_fee', 0)
        
        # Opportunity-specific features
        if opp_type == 'scholarship':
            # Scholarship-specific features
            min_score_match = 1 if (opportunity.get('min_academic_score', 0) <= academic_score) else 0
            income_match = 1 if (opportunity.get('max_income', float('inf')) >= family_income) else 0
            course_match = 1 if self._check_course_match(student_profile, opportunity) else 0
            
            features = [
                academic_score,
                min(academic_score / max(opportunity.get('min_academic_score', 1), 1), 2),
                min(family_income / max(opportunity.get('max_income', family_income), 1), 2),
                extracurriculars,
                skills_count,
                min_score_match,
                income_match,
                course_match
            ]
        else:
            # Work-study specific features
            hours_match = 1 if (opportunity.get('hours_per_week', 0) <= 
                               student_profile.get('preferred_hours', 100)) else 0
            location_match = 1 if self._check_location_match(student_profile, opportunity) else 0
            skills_match_ratio = self._calculate_skills_match(student_profile, opportunity)
            
            features = [
                academic_score,
                family_income / 100000,  # Normalize
                extracurriculars,
                skills_count,
                opportunity.get('stipend', 0) / 10000,  # Normalize stipend
                hours_match,
                location_match,
                skills_match_ratio
            ]
        
        return np.array(features).reshape(1, -1)
    
    def _check_course_match(self, student_profile: Dict, opportunity: Dict) -> bool:
        """Check if student's course matches scholarship eligibility"""
        eligible_courses = opportunity.get('eligible_courses', [])
        if not eligible_courses or 'all' in [c.lower() for c in eligible_courses]:
            return True
        
        student_course = student_profile.get('course', '').lower()
        return any(course.lower() in student_course for course in eligible_courses)
    
    def _check_location_match(self, student_profile: Dict, opportunity: Dict) -> bool:
        """Check if location matches"""
        if opportunity.get('remote'):
            return True
        
        student_location = student_profile.get('preferred_location', '').lower()
        opp_location = opportunity.get('location', '').lower()
        
        if not student_location or not opp_location:
            return True
        
        return student_location in opp_location or opp_location in student_location
    
    def _calculate_skills_match(self, student_profile: Dict, opportunity: Dict) -> float:
        """Calculate percentage of skills that match"""
        student_skills = set([s.lower() for s in student_profile.get('skills', [])])
        required_skills = set([s.lower() for s in opportunity.get('required_skills', [])])
        
        if not required_skills:
            return 1.0
        
        if not student_skills:
            return 0.0
        
        matched = len(student_skills & required_skills)
        return matched / len(required_skills)
    
    def predict_success_rate(self, student_profile: Dict, opportunity: Dict, 
                            opp_type: str) -> float:
        """Predict success probability for an application"""
        if not self.is_trained:
            return 0.5  # Default 50%
        
        try:
            features = self._extract_features_for_matching(student_profile, opportunity, opp_type)
            # Pad features to match model input size if needed
            if features.shape[1] < 5:
                padding = np.zeros((1, 5 - features.shape[1]))
                features = np.hstack([features, padding])
            elif features.shape[1] > 5:
                features = features[:, :5]
            
            success_prob = self.success_model.predict(features)[0]
            return float(np.clip(success_prob, 0, 1))
        except Exception as e:
            print(f"Error predicting success rate: {e}")
            return 0.5
    
    def get_enhanced_match_score(self, student_profile: Dict, opportunity: Dict, 
                                 opp_type: str) -> Tuple[float, Dict]:
        """Get enhanced ML-based match score with explanations"""
        
        # Base rule-based score (0-100)
        rule_score = self._calculate_rule_based_score(student_profile, opportunity, opp_type)
        
        # ML-predicted score
        ml_score = 0
        if self.is_trained:
            try:
                features = self._extract_features_for_matching(student_profile, opportunity, opp_type)
                if opp_type == 'scholarship':
                    ml_score = self.scholarship_model.predict(features)[0]
                else:
                    ml_score = self.work_study_model.predict(features)[0]
                ml_score = float(np.clip(ml_score, 0, 100))
            except Exception as e:
                print(f"ML prediction error: {e}")
                ml_score = rule_score
        
        # Combine scores (70% ML, 30% rules)
        final_score = (ml_score * 0.7) + (rule_score * 0.3)
        
        # Generate explanation
        explanation = self._generate_match_explanation(student_profile, opportunity, opp_type, final_score)
        
        return final_score, explanation
    
    def _calculate_rule_based_score(self, student_profile: Dict, opportunity: Dict, 
                                    opp_type: str) -> float:
        """Calculate rule-based match score"""
        score = 0
        
        if opp_type == 'scholarship':
            # Academic score (30 points)
            min_score = opportunity.get('min_academic_score', 0)
            if min_score:
                if student_profile.get('academic_score', 0) >= min_score:
                    score += 30
                else:
                    return 0  # Fail minimum requirement
            
            # Income criteria (25 points)
            max_income = opportunity.get('max_income')
            if max_income:
                if student_profile.get('family_income', 0) <= max_income:
                    score += 25
                else:
                    return 0
            
            # Course matching (20 points)
            if self._check_course_match(student_profile, opportunity):
                score += 20
            
            # Merit bonus (15 points)
            if opportunity.get('merit_based') and student_profile.get('academic_score', 0) > 85:
                score += 15
            elif opportunity.get('merit_based') and student_profile.get('academic_score', 0) > 75:
                score += 10
            
            # Need bonus (10 points)
            if opportunity.get('need_based') and student_profile.get('family_income', 0) < 50000:
                score += 10
            
        else:  # work_study
            # Skills match (35 points)
            skills_ratio = self._calculate_skills_match(student_profile, opportunity)
            score += skills_ratio * 35
            
            # Hours match (25 points)
            pref_hours = student_profile.get('preferred_hours')
            opp_hours = opportunity.get('hours_per_week', 0)
            if pref_hours:
                hour_diff = abs(opp_hours - pref_hours)
                if hour_diff <= 5:
                    score += 25
                elif hour_diff <= 10:
                    score += 15
                else:
                    score += 5
            else:
                score += 15
            
            # Location match (20 points)
            if opportunity.get('remote'):
                score += 20
            elif self._check_location_match(student_profile, opportunity):
                score += 20
            else:
                score += 5
            
            # Stipend match (20 points)
            expected = student_profile.get('expected_stipend', 0)
            stipend = opportunity.get('stipend', 0)
            if expected:
                if stipend >= expected:
                    score += 20
                elif stipend >= expected * 0.8:
                    score += 15
                else:
                    score += 5
            else:
                score += 10
        
        return score
    
    def _generate_match_explanation(self, student_profile: Dict, opportunity: Dict,
                                   opp_type: str, score: float) -> Dict:
        """Generate detailed explanation for match score"""
        explanation = {
            'score': score,
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }
        
        if opp_type == 'scholarship':
            # Academic strength
            min_score = opportunity.get('min_academic_score', 0)
            student_score = student_profile.get('academic_score', 0)
            if min_score and student_score >= min_score:
                explanation['strengths'].append(f"Excellent academics: {student_score}% (requirement: {min_score}%)")
            elif student_score > 80:
                explanation['strengths'].append(f"Strong academic performance: {student_score}%")
            elif student_score < 60:
                explanation['weaknesses'].append(f"Academic score ({student_score}%) is below average")
                explanation['suggestions'].append("Consider improving grades or applying for need-based scholarships")
            
            # Financial need
            max_income = opportunity.get('max_income')
            family_income = student_profile.get('family_income', 0)
            if max_income and family_income <= max_income:
                if family_income < 50000:
                    explanation['strengths'].append("High financial need - good candidate for need-based funding")
                else:
                    explanation['strengths'].append("Meets income eligibility criteria")
            elif family_income > 100000:
                explanation['weaknesses'].append("Higher family income may limit need-based opportunities")
                explanation['suggestions'].append("Focus on merit-based scholarships and work-study")
            
            # Course match
            if self._check_course_match(student_profile, opportunity):
                explanation['strengths'].append("Your course aligns with scholarship requirements")
            
        else:  # work_study
            # Skills analysis
            skills_match = self._calculate_skills_match(student_profile, opportunity)
            if skills_match > 0.7:
                explanation['strengths'].append(f"Strong skills match ({int(skills_match * 100)}%)")
            elif skills_match > 0.4:
                explanation['strengths'].append(f"Good skills match ({int(skills_match * 100)}%)")
            else:
                missing_skills = set(opportunity.get('required_skills', [])) - set(student_profile.get('skills', []))
                if missing_skills:
                    explanation['weaknesses'].append(f"Missing skills: {', '.join(list(missing_skills)[:3])}")
                    explanation['suggestions'].append("Consider developing these skills through online courses")
            
            # Hours flexibility
            pref_hours = student_profile.get('preferred_hours')
            opp_hours = opportunity.get('hours_per_week', 0)
            if pref_hours:
                if abs(opp_hours - pref_hours) <= 5:
                    explanation['strengths'].append(f"Perfect hours match: {opp_hours} hours/week")
                else:
                    explanation['suggestions'].append(f"Position requires {opp_hours} hours/week - ensure this fits your schedule")
            
            # Location
            if opportunity.get('remote'):
                explanation['strengths'].append("Remote work available - flexible location")
            elif self._check_location_match(student_profile, opportunity):
                explanation['strengths'].append(f"Location matches your preference")
        
        # Add general suggestions based on score
        if score < 40:
            explanation['suggestions'].append("Consider other opportunities that better match your profile")
        elif score > 80:
            explanation['strengths'].append("Excellent match! Strong chances of selection")
        
        return explanation