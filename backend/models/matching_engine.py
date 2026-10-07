import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

class IntelligentMatchingEngine:
    def __init__(self, db):
        self.db = db
        
    def match_scholarships(self, student_profile: Dict) -> List[Dict]:
        """Match student with suitable scholarships"""
        scholarships = self.db.get_scholarships({'status': 'active'})
        
        if not scholarships:
            return []
        
        matches = []
        for scholarship in scholarships:
            # Calculate match score based on multiple criteria
            score = 0
            reasons = []
            
            # 1. Academic score matching (30 points)
            min_score = scholarship.get('min_academic_score', 0)
            if min_score:
                if student_profile.get('academic_score', 0) >= min_score:
                    score += 30
                    reasons.append(f"Meets minimum academic requirement of {min_score}%")
                else:
                    continue  # Minimum requirement not met
            
            # 2. Income criteria (25 points)
            max_income = scholarship.get('max_income')
            if max_income:
                if student_profile.get('family_income', float('inf')) <= max_income:
                    score += 25
                    reasons.append(f"Meets income criteria (≤ ₹{max_income:,.0f})")
                else:
                    continue
            
            # 3. Course/Field matching (20 points)
            eligible_courses = scholarship.get('eligible_courses', [])
            if eligible_courses:
                student_course = student_profile.get('course', '').lower()
                if 'all' in [c.lower() for c in eligible_courses]:
                    score += 15
                    reasons.append("Open to all courses")
                elif any(course.lower() in student_course for course in eligible_courses):
                    score += 20
                    reasons.append("Course matches scholarship criteria")
                else:
                    continue
            
            # 4. Merit-based (15 points)
            if scholarship.get('merit_based'):
                if student_profile.get('academic_score', 0) > 85:
                    score += 15
                    reasons.append("Excellent academic record")
                elif student_profile.get('academic_score', 0) > 75:
                    score += 10
                    reasons.append("Good academic record")
            
            # 5. Need-based (15 points)
            if scholarship.get('need_based'):
                income = student_profile.get('family_income', 100000)
                if income < 50000:
                    score += 15
                    reasons.append("High financial need")
                elif income < 100000:
                    score += 10
                    reasons.append("Moderate financial need")
            
            # 6. Extracurricular activities (10 points)
            if scholarship.get('requires_extracurricular'):
                extracurriculars = student_profile.get('extracurriculars', 0)
                if extracurriculars >= 3:
                    score += 10
                    reasons.append("Strong extracurricular involvement")
                elif extracurriculars >= 1:
                    score += 5
                    reasons.append("Some extracurricular activities")
            
            # Calculate deadline urgency (bonus points)
            if scholarship.get('deadline'):
                try:
                    deadline = datetime.fromisoformat(scholarship['deadline'].replace('Z', '+00:00'))
                    days_left = (deadline - datetime.now()).days
                    if days_left < 30:
                        score += 5  # Urgent - apply soon
                except:
                    pass
            
            matches.append({
                'id': scholarship['id'],
                'title': scholarship['name'],
                'provider': scholarship['provider'],
                'amount': scholarship['amount'],
                'deadline': scholarship.get('deadline'),
                'match_score': score,
                'reasons': reasons,
                'type': 'scholarship'
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]  # Top 10 matches
    
    def match_work_study(self, student_profile: Dict) -> List[Dict]:
        """Match student with work-study opportunities"""
        opportunities = self.db.get_work_study_opportunities({'status': 'open'})
        
        if not opportunities:
            return []
        
        matches = []
        student_skills = set(student_profile.get('skills', []))
        
        for opp in opportunities:
            score = 0
            reasons = []
            
            # 1. Skills matching (30 points)
            required_skills = set(opp.get('required_skills', []))
            if required_skills:
                matching_skills = student_skills.intersection(required_skills)
                if matching_skills:
                    skill_score = min(30, len(matching_skills) * 10)
                    score += skill_score
                    reasons.append(f"Skills match: {', '.join(matching_skills)}")
                elif not student_skills:
                    # No skills listed, give partial credit
                    score += 10
                    reasons.append("No skills specified")
                else:
                    # No matching skills, but don't disqualify
                    score += 5
                    reasons.append("Some skills may be transferable")
            
            # 2. Hours preference (20 points)
            opp_hours = opp.get('hours_per_week', 0)
            pref_hours = student_profile.get('preferred_hours')
            if pref_hours:
                hour_diff = abs(opp_hours - pref_hours)
                if hour_diff <= 5:
                    score += 20
                    reasons.append(f"Perfect hours match ({opp_hours}h/week)")
                elif hour_diff <= 10:
                    score += 15
                    reasons.append(f"Close hours match ({opp_hours}h/week)")
                else:
                    score += 5
                    reasons.append(f"Hours available ({opp_hours}h/week)")
            else:
                score += 10
                reasons.append(f"Flexible hours ({opp_hours}h/week)")
            
            # 3. Location preference (15 points)
            opp_location = opp.get('location', '').lower()
            pref_location = student_profile.get('preferred_location', '').lower()
            
            if opp.get('remote'):
                score += 15
                reasons.append("Remote work available")
            elif pref_location and opp_location:
                if pref_location in opp_location or opp_location in pref_location:
                    score += 15
                    reasons.append(f"Location match: {opp['location']}")
                else:
                    score += 5
                    reasons.append(f"Location: {opp['location']}")
            else:
                score += 10
                reasons.append("Location TBD")
            
            # 4. Stipend vs expectation (20 points)
            opp_stipend = opp.get('stipend', 0)
            exp_stipend = student_profile.get('expected_stipend')
            
            if exp_stipend:
                if opp_stipend >= exp_stipend:
                    score += 20
                    reasons.append(f"Stipend meets expectations (₹{opp_stipend:,.0f}/month)")
                elif opp_stipend >= exp_stipend * 0.8:
                    score += 15
                    reasons.append(f"Good stipend: ₹{opp_stipend:,.0f}/month")
                else:
                    score += 5
                    reasons.append(f"Stipend: ₹{opp_stipend:,.0f}/month")
            else:
                score += 10
                reasons.append(f"Stipend: ₹{opp_stipend:,.0f}/month")
            
            # 5. Duration compatibility (15 points)
            opp_duration = opp.get('duration_months', 6)
            course_duration = student_profile.get('course_duration', 4) * 12  # Convert to months
            
            if opp_duration <= course_duration:
                score += 15
                reasons.append(f"Duration fits ({opp_duration} months)")
            else:
                score += 5
                reasons.append(f"Duration may be long ({opp_duration} months)")
            
            matches.append({
                'id': opp['id'],
                'title': opp['title'],
                'organization': opp['organization'],
                'stipend': opp['stipend'],
                'hours_per_week': opp['hours_per_week'],
                'location': opp.get('location', 'Remote' if opp.get('remote') else 'TBD'),
                'remote': opp.get('remote', False),
                'deadline': opp.get('deadline'),
                'match_score': score,
                'reasons': reasons,
                'type': 'work_study'
            })
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]
    
    def get_personalized_recommendations(self, student_id: str) -> List[Dict]:
        """Get comprehensive personalized recommendations"""
        # Get student profile
        student_profile = self.db.get_student_profile(student_id)
        if not student_profile:
            return []
        
        # Get matches from all sources
        scholarship_matches = self.match_scholarships(student_profile)
        work_study_matches = self.match_work_study(student_profile)
        
        # Combine and sort all opportunities
        all_matches = scholarship_matches + work_study_matches
        all_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return all_matches
    
    def find_students_for_scholarship(self, scholarship_id: str) -> List[Dict]:
        """Find eligible students for a specific scholarship"""
        # Get scholarship
        scholarships = self.db.get_scholarships({'id': scholarship_id})
        if not scholarships:
            return []
        
        scholarship = scholarships[0]
        
        # Get all students with profiles
        students = self.db.get_all_students()
        
        eligible_students = []
        for student in students:
            # Check eligibility criteria
            eligible = True
            score = 0
            
            # Academic score check
            min_score = scholarship.get('min_academic_score')
            if min_score and student.get('academic_score', 0) < min_score:
                eligible = False
            
            # Income check
            max_income = scholarship.get('max_income')
            if max_income and student.get('family_income', float('inf')) > max_income:
                eligible = False
            
            if eligible:
                # Calculate match score
                if student.get('academic_score', 0) > 85:
                    score += 30
                elif student.get('academic_score', 0) > 75:
                    score += 20
                else:
                    score += 10
                
                income = student.get('family_income', 100000)
                if income < 50000:
                    score += 25
                elif income < 100000:
                    score += 15
                
                eligible_students.append({
                    'student': {
                        'id': student['id'],
                        'name': student.get('name', 'Unknown'),
                        'email': student.get('email', ''),
                        'academic_score': student.get('academic_score'),
                        'family_income': student.get('family_income'),
                        'course': student.get('course')
                    },
                    'match_score': score
                })
        
        eligible_students.sort(key=lambda x: x['match_score'], reverse=True)
        return eligible_students[:20]