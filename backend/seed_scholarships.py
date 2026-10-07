# add_sample_scholarships_with_links.py
from models.database import Database
import json

def add_sample_scholarships():
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Clear existing (optional)
    cursor.execute("DELETE FROM scholarships")
    
    sample_scholarships = [
        {
            'name': 'INSPIRE Scholarship - SHE',
            'provider': 'Department of Science & Technology',
            'description': 'Scholarship for Higher Education (SHE) for students pursuing basic sciences',
            'amount': 80000.0,
            'deadline': '2026-12-31',
            'link': 'https://www.online-inspire.gov.in/',
            'min_academic_score': 90,
            'max_income': 150000,
            'eligible_courses': json.dumps(['B.Sc', 'M.Sc', 'BS-MS']),
            'merit_based': 1,
            'need_based': 1,
            'requires_extracurricular': 0,
            'status': 'active',
            'total_slots': 100
        },
        {
            'name': 'National Scholarship Portal',
            'provider': 'Ministry of Education',
            'description': 'Central portal for all government scholarships',
            'amount': 50000.0,
            'deadline': '2026-11-30',
            'link': 'https://scholarships.gov.in/',
            'min_academic_score': 85,
            'max_income': 300000,
            'eligible_courses': json.dumps(['all']),
            'merit_based': 1,
            'need_based': 0,
            'requires_extracurricular': 1,
            'status': 'active',
            'total_slots': 200
        },
        {
            'name': 'Post-Matric Scholarship',
            'provider': 'State Government',
            'description': 'For SC/ST students pursuing higher education',
            'amount': 30000.0,
            'deadline': '2026-10-15',
            'link': 'https://www.buddy4study.com/',
            'min_academic_score': 75,
            'max_income': 250000,
            'eligible_courses': json.dumps(['all']),
            'merit_based': 0,
            'need_based': 1,
            'requires_extracurricular': 0,
            'status': 'active',
            'total_slots': 500
        },
        {
            'name': 'AICTE Pragati Scholarship',
            'provider': 'AICTE',
            'description': 'Scholarship for girl students in technical education',
            'amount': 50000.0,
            'deadline': '2026-09-30',
            'link': 'https://www.aicte-india.org/schemes/students-development-schemes',
            'min_academic_score': 80,
            'max_income': 200000,
            'eligible_courses': json.dumps(['B.Tech', 'M.Tech', 'Diploma']),
            'merit_based': 1,
            'need_based': 1,
            'requires_extracurricular': 0,
            'status': 'active',
            'total_slots': 150
        },
        {
            'name': 'Prime Minister\'s Scholarship Scheme',
            'provider': 'Central Government',
            'description': 'For wards of ex-servicemen',
            'amount': 25000.0,
            'deadline': '2026-08-31',
            'link': 'https://www.desw.gov.in/',
            'min_academic_score': 70,
            'max_income': 400000,
            'eligible_courses': json.dumps(['all']),
            'merit_based': 0,
            'need_based': 1,
            'requires_extracurricular': 0,
            'status': 'active',
            'total_slots': 300
        }
    ]
    
    for s in sample_scholarships:
        cursor.execute('''
            INSERT INTO scholarships (
                name, provider, description, amount, deadline, link,
                min_academic_score, max_income, eligible_courses,
                merit_based, need_based, requires_extracurricular,
                status, total_slots, applications_received
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            s['name'],
            s['provider'],
            s['description'],
            s['amount'],
            s['deadline'],
            s['link'],
            s['min_academic_score'],
            s['max_income'],
            s['eligible_courses'],
            s['merit_based'],
            s['need_based'],
            s['requires_extracurricular'],
            s['status'],
            s['total_slots']
        ))
        print(f"✅ Added: {s['name']}")
    
    conn.commit()
    conn.close()
    print("\n✅ All scholarships added with links!")

if __name__ == "__main__":
    add_sample_scholarships()