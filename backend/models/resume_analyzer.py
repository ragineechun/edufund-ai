# models/resume_analyzer.py - COMPLETE FIXED VERSION
import re
import os
import PyPDF2
import docx
from textblob import TextBlob
import nltk
from typing import Dict, List, Set, Optional
from collections import Counter

class ResumeAnalyzer:
    def __init__(self):
        # Expanded skill database
        self.skill_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'sql', 'html', 'css', 'react', 'node.js', 
                           'django', 'flask', 'spring', 'angular', 'vue', 'typescript', 'php', 'ruby', 'go',
                           'c#', 'ruby', 'perl', 'swift', 'kotlin', 'rust'],
            'data_science': ['machine learning', 'data analysis', 'tensorflow', 'pytorch', 'pandas', 'numpy',
                           'scikit-learn', 'deep learning', 'nlp', 'computer vision', 'tableau', 'power bi',
                           'data visualization', 'statistics', 'r', 'matplotlib', 'seaborn'],
            'cloud_devops': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'linux',
                           'terraform', 'ansible', 'devops', 'cloud computing'],
            'design': ['photoshop', 'illustrator', 'figma', 'ui/ux', 'graphic design', 'adobe xd', 'sketch',
                      'after effects', 'premiere pro', 'canva'],
            'communication': ['public speaking', 'presentation', 'writing', 'editing', 'content creation', 
                            'storytelling', 'negotiation', 'copywriting', 'blogging'],
            'leadership': ['team lead', 'project management', 'supervisor', 'coordinator', 'manager',
                         'scrum master', 'agile', 'leadership', 'mentoring', 'team management'],
            'languages': ['english', 'hindi', 'spanish', 'french', 'german', 'mandarin', 'japanese',
                         'korean', 'russian', 'arabic'],
            'soft_skills': ['communication', 'teamwork', 'problem solving', 'critical thinking', 'time management',
                          'adaptability', 'creativity', 'collaboration', 'emotional intelligence', 'work ethic']
        }
        
        # Common degree patterns
        self.degree_patterns = [
            r'(B\.?[A-Z]\.?\s*[A-Z]*|[M]\.?[A-Z]\.?\s*[A-Z]*|Ph\.?D\.?)',
            r'(Bachelor|Master|Doctorate|Associate)\s+(of\s+)?([A-Za-z\s]+)',
            r'(B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|B\.?A|M\.?A|MBA|MCA|BCA|MCA)',
            r'(Bachelor of|Master of|Doctor of)\s+([A-Za-z\s]+)'
        ]
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        print(f"Error extracting page {page_num}: {e}")
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = docx.Document(file_path)
            # Extract from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + " "
                    text += "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        text = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
            except Exception as e:
                print(f"Error reading TXT: {e}")
        return text
    
    def extract_text(self, file_path: str) -> str:
        """Main method to extract text from resume file"""
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return ""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file format: {file_ext}")
            return ""
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Enhanced skill extraction with better pattern matching"""
        text_lower = text.lower()
        skills = {category: [] for category in self.skill_keywords.keys()}
        
        for category, keywords in self.skill_keywords.items():
            for keyword in keywords:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    skills[category].append(keyword)
        
        # Remove duplicates within category
        for category in skills:
            skills[category] = list(set(skills[category]))
        
        return skills
    
    def extract_education(self, text: str) -> List[Dict]:
        """Enhanced education extraction with better pattern matching"""
        education = []
        lines = text.split('\n')
        
        for line in lines:
            # Skip short lines
            if len(line.strip()) < 10:
                continue
            
            edu_item = {}
            
            # Check for degree patterns
            for pattern in self.degree_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    edu_item['degree'] = match.group(0).strip()
                    break
            
            # If degree found, look for other details
            if edu_item:
                # Extract year
                year_match = re.search(r'(20\d{2})', line)
                if year_match:
                    edu_item['year'] = year_match.group(0)
                
                # Extract institution
                inst_patterns = [
                    r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'university\s+of\s+([A-Za-z\s]+)',
                    r'([A-Z][a-z]+)\s+(University|College|Institute|School)',
                    r'(IIT|NIT|IIIT|BITS|MIT|Stanford|Harvard|Oxford|Cambridge)'
                ]
                
                for pattern in inst_patterns:
                    inst_match = re.search(pattern, line, re.IGNORECASE)
                    if inst_match:
                        edu_item['institution'] = inst_match.group(0).replace('at ', '').replace('from ', '').strip()
                        break
                
                # Extract score/percentage
                score_match = re.search(r'(\d+\.?\d*)\s*%', line)
                if score_match:
                    edu_item['score'] = float(score_match.group(1))
                else:
                    # Extract GPA
                    gpa_match = re.search(r'GPA:\s*(\d+\.?\d*)', line, re.IGNORECASE)
                    if gpa_match:
                        edu_item['gpa'] = float(gpa_match.group(1))
                
                education.append(edu_item)
        
        return education
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Enhanced experience extraction"""
        experiences = []
        lines = text.split('\n')
        
        current_exp = {}
        exp_section = False
        
        for i, line in enumerate(lines):
            # Look for date ranges
            date_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)', line, re.IGNORECASE)
            if date_match:
                exp_section = True
                if current_exp and 'position' in current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    'start_date': date_match.group(1),
                    'end_date': date_match.group(2) if date_match.group(2).lower() not in ['present', 'current', 'now'] else 'Present'
                }
                continue
            
            # Look for position titles (usually short lines with keywords)
            position_keywords = ['developer', 'engineer', 'analyst', 'manager', 'intern', 'associate', 
                               'consultant', 'specialist', 'coordinator', 'designer', 'architect',
                               'scientist', 'researcher', 'lead', 'senior', 'junior']
            
            if exp_section and len(line.strip()) < 60 and any(kw in line.lower() for kw in position_keywords):
                if 'position' not in current_exp:
                    current_exp['position'] = line.strip()
                continue
            
            # Look for company names
            company_keywords = ['inc', 'corp', 'ltd', 'technologies', 'solutions', 'systems', 'company',
                              'labs', 'enterprises', 'group', 'foundation', 'institute']
            if exp_section and any(kw in line.lower() for kw in company_keywords):
                if 'company' not in current_exp:
                    current_exp['company'] = line.strip()
                continue
            
            # If we have position but no company, check next line
            if exp_section and 'position' in current_exp and 'company' not in current_exp and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if len(next_line) < 60 and next_line and any(kw in next_line.lower() for kw in company_keywords):
                    current_exp['company'] = next_line
        
        # Add the last experience
        if current_exp and 'position' in current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def extract_projects(self, text: str) -> List[str]:
        """Enhanced project extraction"""
        projects = []
        lines = text.split('\n')
        
        project_keywords = ['project:', 'developed', 'built', 'created', 'implemented', 'designed',
                           'worked on', 'contributed to', 'led', 'architected']
        project_section = False
        current_project = ""
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for project section header
            if 'project' in line_lower and (':' in line or len(line.split()) < 6):
                project_section = True
                if current_project:
                    projects.append(current_project.strip())
                    current_project = ""
                continue
            
            # Extract project descriptions
            if project_section and len(line.strip()) > 15:
                if any(kw in line_lower for kw in project_keywords):
                    if current_project:
                        projects.append(current_project.strip())
                    current_project = line.strip()
                elif current_project and len(current_project) < 150:
                    current_project += " " + line.strip()
        
        # Add the last project
        if current_project:
            projects.append(current_project.strip())
        
        # Also look for bullet points throughout the document
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '→', '✓')) and len(line) > 15:
                if any(kw in line.lower() for kw in project_keywords):
                    projects.append(line.lstrip('•-*→✓ '))
        
        # Remove duplicates and limit
        projects = list(dict.fromkeys(projects))[:5]
        
        return projects
    
    def analyze_resume(self, file_path: str) -> Dict:
        """Complete resume analysis with better formatting"""
        # Check if file exists
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        # Extract text
        text = self.extract_text(file_path)
        
        if not text or len(text.strip()) < 50:
            return {'error': 'Could not extract text from file. File may be empty or corrupted.'}
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines
        text = text.strip()
        
        # Extract information
        skills = self.extract_skills(text)
        education = self.extract_education(text)
        experience = self.extract_experience(text)
        projects = self.extract_projects(text)
        
        # Calculate metrics
        total_skills = sum(len(skills[cat]) for cat in skills)
        skills_diversity = len([cat for cat in skills if skills[cat]]) / len(skills) if skills else 0
        
        # Sentiment analysis (for positive/negative language)
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
        except:
            sentiment = 0
        
        # Readability score (average words per sentence)
        try:
            sentences = nltk.sent_tokenize(text)
            avg_words = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
            readability_score = min(avg_words / 20, 1)
        except:
            readability_score = 0.5
        
        # Estimate years of experience from dates
        total_years = 0
        current_year = 2026
        for exp in experience:
            if exp.get('start_date') and exp.get('end_date'):
                try:
                    start = int(exp['start_date'])
                    end = int(exp['end_date']) if exp['end_date'].lower() != 'present' else current_year
                    if start and end and end > start:
                        total_years += (end - start)
                except:
                    pass
        
        # Calculate skill categories with most skills
        top_categories = []
        for category, skills_list in skills.items():
            if skills_list:
                top_categories.append({'category': category, 'count': len(skills_list)})
        top_categories.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'skills': skills,
            'total_skills': total_skills,
            'skills_diversity': skills_diversity,
            'top_skill_categories': top_categories[:3],
            'education': education,
            'experience': experience,
            'projects': projects,
            'metrics': {
                'total_experience_years': total_years,
                'total_projects': len(projects),
                'education_level': len(education),
                'sentiment_score': sentiment,
                'readability_score': readability_score,
                'total_skills_detected': total_skills
            },
            'extracted_text_preview': text[:500] + '...' if len(text) > 500 else text,
            'file_name': os.path.basename(file_path)
        }
    
    def extract_student_profile_from_resume(self, file_path: str) -> Dict:
        """Extract profile information to populate student form"""
        analysis = self.analyze_resume(file_path)
        
        if 'error' in analysis:
            return {}
        
        # Build profile data
        profile = {
            'skills': [],
            'extracurriculars': 0,
            'academic_score': None,
            'course': None,
            'institution': None
        }
        
        # Extract all skills
        for category, skills in analysis['skills'].items():
            profile['skills'].extend(skills)
        
        # Estimate extracurriculars from projects and other activities
        profile['extracurriculars'] = len(analysis['projects']) + (analysis['metrics']['total_projects'] // 2)
        
        # Try to extract academic score from education
        for edu in analysis['education']:
            if 'score' in edu and edu['score']:
                profile['academic_score'] = edu['score']
                break
            elif 'gpa' in edu and edu['gpa']:
                # Convert GPA to percentage (assuming 10-point scale)
                profile['academic_score'] = edu['gpa'] * 10
                break
        
        # Try to extract course from education
        for edu in analysis['education']:
            if edu.get('degree'):
                profile['course'] = edu['degree']
                break
        
        # Try to extract institution from education
        for edu in analysis['education']:
            if edu.get('institution'):
                profile['institution'] = edu['institution']
                break
        
        # Clean up
        profile['skills'] = list(set(profile['skills']))[:15]  # Remove duplicates, limit to 15
        
        return profile


# Test function
if __name__ == "__main__":
    # Quick test
    analyzer = ResumeAnalyzer()
    
    # Test with sample text
    sample_text = """John Doe
    Python Developer with 3 years experience
    Education: B.Tech Computer Science from MIT, 2020, GPA: 8.5
    Skills: Python, Machine Learning, React, SQL, AWS
    Projects: Built an AI-powered recommendation system
    Experience: Software Engineer at TechCorp (2021-2024)"""
    
    # Create temporary file
    with open('test_temp.txt', 'w') as f:
        f.write(sample_text)
    
    # Analyze
    result = analyzer.analyze_resume('test_temp.txt')
    
    print("=== Test Results ===")
    print(f"Total Skills: {result['total_skills']}")
    print(f"Education: {len(result['education'])} entries")
    print(f"Experience: {len(result['experience'])} entries")
    print(f"Projects: {len(result['projects'])} entries")
    
    # Clean up
    import os
    os.remove('test_temp.txt')