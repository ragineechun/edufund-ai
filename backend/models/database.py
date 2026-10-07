import sqlite3
import os
from datetime import datetime
import bcrypt
import json
import traceback

class Database:
    def __init__(self, db_path='database/edufund.db'):
        self.db_path = db_path
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        print("✅ SQLite Database connected successfully!")
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                profile_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                academic_score REAL,
                family_income REAL,
                extracurriculars INTEGER,
                siblings_education INTEGER,
                course TEXT,
                institution TEXT,
                course_duration INTEGER,
                tuition_fee REAL,
                skills TEXT,
                preferred_location TEXT,
                preferred_hours INTEGER,
                expected_stipend REAL,
                profile_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Scholarships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scholarships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                deadline DATE,
                link TEXT,
                min_academic_score REAL,
                max_income REAL,
                eligible_courses TEXT,
                merit_based INTEGER DEFAULT 0,
                need_based INTEGER DEFAULT 0,
                requires_extracurricular INTEGER DEFAULT 0,
                other_requirements TEXT,
                status TEXT DEFAULT 'active',
                total_slots INTEGER,
                applications_received INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Databases created before the 'link' column existed get it added here
        cursor.execute('PRAGMA table_info(scholarships)')
        if 'link' not in [row[1] for row in cursor.fetchall()]:
            cursor.execute('ALTER TABLE scholarships ADD COLUMN link TEXT')

        # Work-study table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_study (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                organization TEXT NOT NULL,
                description TEXT,
                stipend REAL NOT NULL,
                hours_per_week INTEGER NOT NULL,
                duration_months INTEGER,
                location TEXT,
                remote INTEGER DEFAULT 0,
                required_skills TEXT,
                deadline DATE,
                status TEXT DEFAULT 'open',
                positions_available INTEGER DEFAULT 1,
                applicants INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crowdfunding campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crowdfunding_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                story TEXT,
                goal_amount REAL NOT NULL,
                raised_amount REAL DEFAULT 0,
                deadline DATE,
                category TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')
        
        # Donations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                donor_name TEXT,
                donor_email TEXT,
                amount REAL NOT NULL,
                message TEXT,
                anonymous INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES crowdfunding_campaigns (id) ON DELETE CASCADE
            )
        ''')
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                opportunity_id INTEGER NOT NULL,
                opportunity_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                message TEXT,
                documents TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')
        
        # Blockchain transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blockchain_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_hash TEXT UNIQUE,
                previous_hash TEXT,
                block_index INTEGER,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database tables created/verified")
    
   
    
    def create_user(self, email, password, name, role='student'):
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, name, role)
                VALUES (?, ?, ?, ?)
            ''', (email, password_hash, name, role))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            # Get created user
            cursor.execute('SELECT id, email, name, role, created_at FROM users WHERE id = ?', (user_id,))
            user = dict(cursor.fetchone())
            
            conn.close()
            return user
            
        except sqlite3.IntegrityError:
            print(f"User with email {email} already exists")
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                if bcrypt.checkpw(password.encode('utf-8'), user_dict['password_hash'].encode('utf-8')):
                    user_dict.pop('password_hash', None)
                    conn.close()
                    return user_dict
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            # Convert to int if string
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                except ValueError:
                    print(f"Invalid user_id format: {user_id}")
                    return None
                    
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, email, name, role, profile_completed, created_at FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            conn.close()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
        
    
    def get_all_users(self, role=None):
        """Get all users (admin only)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if role:
                cursor.execute('SELECT id, email, name, role, profile_completed, created_at FROM users WHERE role = ?', (role,))
            else:
                cursor.execute('SELECT id, email, name, role, profile_completed, created_at FROM users')
            
            users = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return users
            
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    #Student Profile Management 
    def create_student_profile(self, user_id, profile_data):
        """Create or update student profile"""
        try:
            # Ensure user_id is int
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                    print(f"Converted user_id from string to int: {user_id}")
                except ValueError:
                    print(f"Failed to convert user_id to int: {user_id}")
                    return None
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First check if user exists
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                print(f"User {user_id} does not exist in database")
                conn.close()
                return None
            
            # Check if profile exists
            cursor.execute('SELECT id FROM student_profiles WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            # Convert lists to JSON strings
            skills = json.dumps(profile_data.get('skills', []))
            
            # Get values with defaults
            academic_score = profile_data.get('academic_score')
            family_income = profile_data.get('family_income')
            extracurriculars = profile_data.get('extracurriculars', 0)
            siblings_education = profile_data.get('siblings_education', 0)
            course = profile_data.get('course', '')
            institution = profile_data.get('institution', '')
            course_duration = profile_data.get('course_duration', 4)
            tuition_fee = profile_data.get('tuition_fee', 0)
            preferred_location = profile_data.get('preferred_location')
            preferred_hours = profile_data.get('preferred_hours')
            expected_stipend = profile_data.get('expected_stipend')
            
            print(f"Inserting/Updating profile for user_id: {user_id}")
            print(f"Profile data: academic_score={academic_score}, family_income={family_income}, course={course}")
            
            if existing:
                # Update existing profile
                cursor.execute('''
                    UPDATE student_profiles SET
                        academic_score = ?,
                        family_income = ?,
                        extracurriculars = ?,
                        siblings_education = ?,
                        course = ?,
                        institution = ?,
                        course_duration = ?,
                        tuition_fee = ?,
                        skills = ?,
                        preferred_location = ?,
                        preferred_hours = ?,
                        expected_stipend = ?,
                        profile_completed = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    academic_score,
                    family_income,
                    extracurriculars,
                    siblings_education,
                    course,
                    institution,
                    course_duration,
                    tuition_fee,
                    skills,
                    preferred_location,
                    preferred_hours,
                    expected_stipend,
                    user_id
                ))
                print(f"Updated existing profile for user {user_id}")
            else:
                # Insert new profile
                cursor.execute('''
                    INSERT INTO student_profiles (
                        user_id, academic_score, family_income, extracurriculars,
                        siblings_education, course, institution, course_duration,
                        tuition_fee, skills, preferred_location, preferred_hours,
                        expected_stipend, profile_completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    user_id,
                    academic_score,
                    family_income,
                    extracurriculars,
                    siblings_education,
                    course,
                    institution,
                    course_duration,
                    tuition_fee,
                    skills,
                    preferred_location,
                    preferred_hours,
                    expected_stipend
                ))
                print(f"Inserted new profile for user {user_id}")
            
            # Update user profile_completed status
            cursor.execute('UPDATE users SET profile_completed = 1 WHERE id = ?', (user_id,))
            
            conn.commit()
            
            # Get the created/updated profile
            cursor.execute('SELECT * FROM student_profiles WHERE user_id = ?', (user_id,))
            profile_row = cursor.fetchone()
            
            if profile_row:
                # Get column names
                cursor.execute('PRAGMA table_info(student_profiles)')
                columns = [col[1] for col in cursor.fetchall()]
                
                # Convert to dict
                profile_dict = dict(zip(columns, profile_row))
                
                # Parse skills
                if profile_dict.get('skills'):
                    try:
                        profile_dict['skills'] = json.loads(profile_dict['skills'])
                    except:
                        profile_dict['skills'] = []
                
                conn.close()
                return profile_dict
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error creating student profile: {e}")
            import traceback
            traceback.print_exc()
            return None
   
    def get_student_profile(self, user_id):
        """Get student profile by user ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sp.*, u.email, u.name 
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.user_id = ?
            ''', (user_id,))
            
            profile = cursor.fetchone()
            conn.close()
            
            if profile:
                profile_dict = dict(profile)
                # Parse JSON skills safely
                if profile_dict.get('skills'):
                    try:
                        profile_dict['skills'] = json.loads(profile_dict['skills'])
                    except:
                        profile_dict['skills'] = []
                return profile_dict
            return None
            
        except Exception as e:
            print(f"Error getting student profile: {e}")
            return None
    def get_all_students(self):
        """Get all students with profiles"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sp.*, u.email, u.name 
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
            ''')
            
            students = []
            for row in cursor.fetchall():
                student = dict(row)
                if student.get('skills'):
                    student['skills'] = json.loads(student['skills'])
                students.append(student)
            
            conn.close()
            return students
            
        except Exception as e:
            print(f"Error getting all students: {e}")
            return []
    
    #Scholarship Management
    
    def add_scholarship(self, scholarship_data):
        """Add a new scholarship"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert lists to JSON
            eligible_courses = json.dumps(scholarship_data.get('eligible_courses', []))
            
            cursor.execute('''
                INSERT INTO scholarships (
                    name, provider, description, amount, deadline, link,
                    min_academic_score, max_income, eligible_courses,
                    merit_based, need_based, requires_extracurricular,
                    other_requirements, status, total_slots, applications_received
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                scholarship_data['name'],
                scholarship_data['provider'],
                scholarship_data.get('description', ''),
                scholarship_data['amount'],
                scholarship_data.get('deadline'),
                scholarship_data.get('link', ''),  
                scholarship_data.get('min_academic_score'),
                scholarship_data.get('max_income'),
                eligible_courses,
                1 if scholarship_data.get('merit_based') else 0,
                1 if scholarship_data.get('need_based') else 0,
                1 if scholarship_data.get('requires_extracurricular') else 0,
                scholarship_data.get('other_requirements', ''),
                'active',
                scholarship_data.get('total_slots')
            ))
            
            conn.commit()
            scholarship_id = cursor.lastrowid
            conn.close()
            
            return scholarship_id
            
        except Exception as e:
            print(f"Error adding scholarship: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def update_scholarship(self, scholarship_id, update_data):
        """Update scholarship details"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            fields = []
            params = []
            
            for key, value in update_data.items():
                if key == 'eligible_courses':
                    value = json.dumps(value)
                fields.append(f"{key} = ?")
                params.append(value)
            
            params.append(scholarship_id)
            
            query = f'''
                UPDATE scholarships 
                SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error updating scholarship: {e}")
            traceback.print_exc()
            return False
    
    def get_scholarships(self, filters=None):
        """Get scholarships with optional filters"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM scholarships'
            params = []
            
            if filters and len(filters) > 0:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            
            scholarships = []
            for row in cursor.fetchall():
                scholarship = dict(row)
                
                if scholarship.get('eligible_courses'):
                    try:
                        scholarship['eligible_courses'] = json.loads(scholarship['eligible_courses'])
                    except:
                        scholarship['eligible_courses'] = []
                scholarships.append(scholarship)
            
            conn.close()
            return scholarships
            
        except Exception as e:
            print(f"Error getting scholarships: {e}")
            return []
        
        
    # Work-Study Management 
    
    def add_work_study(self, work_study_data):
        """Add a work-study opportunity"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert lists to JSON
            required_skills = json.dumps(work_study_data.get('required_skills', []))
            
            cursor.execute('''
                INSERT INTO work_study (
                    title, organization, description, stipend,
                    hours_per_week, duration_months, location,
                    remote, required_skills, deadline, positions_available
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                work_study_data['title'],
                work_study_data['organization'],
                work_study_data.get('description', ''),
                work_study_data['stipend'],
                work_study_data['hours_per_week'],
                work_study_data.get('duration_months', 6),
                work_study_data.get('location', ''),
                1 if work_study_data.get('remote') else 0,
                required_skills,
                work_study_data.get('deadline'),
                work_study_data.get('positions_available', 1)
            ))
            
            conn.commit()
            work_study_id = cursor.lastrowid
            conn.close()
            
            return work_study_id
            
        except Exception as e:
            print(f"Error adding work-study: {e}")
            return None
    
    def get_work_study_opportunities(self, filters=None):
        """Get work-study opportunities"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM work_study'
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            opportunities = []
            
            for row in cursor.fetchall():
                opp = dict(row)
                # Parse JSON skills
                if opp.get('required_skills'):
                    opp['required_skills'] = json.loads(opp['required_skills'])
                opportunities.append(opp)
            
            conn.close()
            return opportunities
            
        except Exception as e:
            print(f"Error getting work-study: {e}")
            return []
    
    # Crowdfunding Management 
    
    
    def create_campaign(self, campaign_data, image_path=None):
        """Create a crowdfunding campaign with proper date handling"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Handle deadline properly
            deadline = campaign_data.get('deadline')
            if deadline:
                # Ensure deadline is in YYYY-MM-DD format
                if isinstance(deadline, str):
                    # If it already has time, extract just the date
                    if 'T' in deadline:
                        deadline = deadline.split('T')[0]
                elif isinstance(deadline, datetime):
                    deadline = deadline.strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO crowdfunding_campaigns (
                    student_id, student_name, title, description,
                    story, goal_amount, deadline, category, image_path,
                    raised_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active')
            ''', (
                campaign_data['student_id'],
                campaign_data['student_name'],
                campaign_data['title'],
                campaign_data.get('description', ''),
                campaign_data.get('story', ''),
                campaign_data['goal_amount'],
                deadline,
                campaign_data.get('category', 'education'),
                image_path
            ))
            
            conn.commit()
            campaign_id = cursor.lastrowid
            conn.close()
            
            return campaign_id
            
        except Exception as e:
            print(f"Error creating campaign: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_campaigns(self, filters=None):
        """Get crowdfunding campaigns"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM crowdfunding_campaigns'
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            else:
                query += ' WHERE status = "active"'
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            campaigns = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return campaigns
            
        except Exception as e:
            print(f"Error getting campaigns: {e}")
            return []
    
    def get_campaign(self, campaign_id):
        """Get a specific campaign"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM crowdfunding_campaigns WHERE id = ?', (campaign_id,))
            campaign = cursor.fetchone()
            
            if campaign:
                campaign = dict(campaign)
                # Get donations
                cursor.execute('SELECT * FROM donations WHERE campaign_id = ? ORDER BY created_at DESC', (campaign_id,))
                campaign['donations'] = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return campaign
            
        except Exception as e:
            print(f"Error getting campaign: {e}")
            return None
    
    
    def donate_to_campaign(self, campaign_id, donor_data):
        """Process a donation with proper amount update"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Add donation record
            cursor.execute('''
                INSERT INTO donations (
                    campaign_id, donor_name, donor_email,
                    amount, message, anonymous
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                donor_data.get('name', 'Anonymous'),
                donor_data.get('email'),
                donor_data['amount'],
                donor_data.get('message', ''),
                1 if donor_data.get('anonymous') else 0
            ))
            
            # Update campaign raised amount
            cursor.execute('''
                UPDATE crowdfunding_campaigns 
                SET raised_amount = raised_amount + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (donor_data['amount'], campaign_id))
            
            # Check if update was successful
            if cursor.rowcount == 0:
                conn.rollback()
                conn.close()
                return False
            
            # Commit transaction
            conn.commit()
            
            # Get updated campaign to verify
            cursor.execute('SELECT raised_amount, goal_amount FROM crowdfunding_campaigns WHERE id = ?', (campaign_id,))
            updated = cursor.fetchone()
            
            conn.close()
            
            if updated:
                print(f"Donation processed: +₹{donor_data['amount']}, New total: ₹{updated[0]} / ₹{updated[1]}")
            
            return True
            
        except Exception as e:
            print(f"Error processing donation: {e}")
            import traceback
            traceback.print_exc()
            return False
   
    # Applications Management
    
    def submit_application(self, application_data):
        """Submit an application"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert documents to JSON
            documents = json.dumps(application_data.get('documents', []))
            
            cursor.execute('''
                INSERT INTO applications (
                    student_id, opportunity_id, opportunity_type,
                    message, documents, status
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                application_data['student_id'],
                application_data['opportunity_id'],
                application_data['opportunity_type'],
                application_data.get('message', ''),
                documents,
                'pending'
            ))
            
            conn.commit()
            application_id = cursor.lastrowid
            
            # Update applicant count
            if application_data['opportunity_type'] == 'scholarship':
                cursor.execute('''
                    UPDATE scholarships 
                    SET applications_received = applications_received + 1 
                    WHERE id = ?
                ''', (application_data['opportunity_id'],))
            else:
                cursor.execute('''
                    UPDATE work_study 
                    SET applicants = applicants + 1 
                    WHERE id = ?
                ''', (application_data['opportunity_id'],))
            
            conn.commit()
            conn.close()
            
            return application_id
            
        except Exception as e:
            print(f"Error submitting application: {e}")
            return None
    
    def get_student_applications(self, student_id):
        """Get student applications"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM applications 
                WHERE student_id = ? 
                ORDER BY applied_at DESC
            ''', (student_id,))
            
            applications = []
            for row in cursor.fetchall():
                app = dict(row)
                if app.get('documents'):
                    app['documents'] = json.loads(app['documents'])
                applications.append(app)
            
            conn.close()
            return applications
            
        except Exception as e:
            print(f"Error getting applications: {e}")
            return []
    
    #Admin Stats 
    
    def get_admin_stats(self):
        """Get admin dashboard statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = "student"')
            total_students = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM scholarships WHERE status = "active"')
            active_scholarships = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM scholarships')
            total_scholarships = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM crowdfunding_campaigns WHERE status = "active"')
            active_campaigns = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM crowdfunding_campaigns')
            total_campaigns = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM applications')
            total_applications = cursor.fetchone()[0]
            
            # Get recent applications
            cursor.execute('''
                SELECT a.*, u.name as student_name 
                FROM applications a
                JOIN users u ON a.student_id = u.id
                ORDER BY a.applied_at DESC LIMIT 5
            ''')
            
            recent_applications = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_students': total_students,
                'total_scholarships': total_scholarships,
                'active_scholarships': active_scholarships,
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_applications': total_applications,
                'recent_applications': recent_applications
            }
            
        except Exception as e:
            print(f"Error getting admin stats: {e}")
            return {
                'total_students': 0,
                'total_scholarships': 0,
                'active_scholarships': 0,
                'total_campaigns': 0,
                'active_campaigns': 0,
                'total_applications': 0,
                'recent_applications': []
            }