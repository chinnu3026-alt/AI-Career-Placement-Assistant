import os
import sqlite3
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g, make_response, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from pypdf import PdfReader
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai-career-placement-assistant-secret-key-1337')

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# PDF Helper Classes
# -------------------------------------------------------------
class PDFReport(FPDF):
    def header(self):
        # Draw dark blue header banner
        self.set_fill_color(37, 99, 235)
        self.rect(0, 0, 210, 30, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'AI CAREER & PLACEMENT ASSISTANT', ln=1, align='C')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, 'Production-Ready Analytical Report', ln=1, align='C')
        self.ln(12)
        
    def footer(self):
        self.set_y(-15)
        self.set_text_color(156, 163, 175)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Automated Report System', align='C')

# -------------------------------------------------------------
# Database Utility & Schemas
# -------------------------------------------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Schema migration check: If old users table does not have 'is_admin' column, recreate tables
        try:
            cursor.execute("SELECT is_admin FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP TABLE IF EXISTS resumes")
            cursor.execute("DROP TABLE IF EXISTS skills")
            cursor.execute("DROP TABLE IF EXISTS certifications")
            cursor.execute("DROP TABLE IF EXISTS projects")
            cursor.execute("DROP TABLE IF EXISTS jobs")
            cursor.execute("DROP TABLE IF EXISTS interviews")
            db.commit()
            
        # 1. users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                cgpa REAL,
                branch TEXT,
                gender TEXT,
                profile_picture TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Ensure branch column exists (for migrating old databases)
        try:
            cursor.execute("SELECT branch FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN branch TEXT")
            db.commit()

        # Ensure gender column exists
        try:
            cursor.execute("SELECT gender FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
            db.commit()

        # Ensure profile_picture column exists
        try:
            cursor.execute("SELECT profile_picture FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
            db.commit()
        
        # 2. resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                extracted_text TEXT,
                ats_score INTEGER,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 3. skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                proficiency TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 4. certifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cert_name TEXT NOT NULL,
                issuing_org TEXT,
                issue_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 5. projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                technologies TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 6. jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                description TEXT,
                requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 7. interviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                question_type TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 8. companies table (Recreated with all company predictor fields)
        cursor.execute('DROP TABLE IF EXISTS companies')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                type TEXT NOT NULL,
                branches TEXT NOT NULL,
                min_cgpa REAL NOT NULL,
                tech_skills TEXT NOT NULL,
                soft_skills TEXT NOT NULL,
                pref_certs TEXT NOT NULL,
                pref_projects TEXT NOT NULL,
                hiring_roles TEXT NOT NULL,
                package_range TEXT NOT NULL,
                logo_url TEXT,
                hq TEXT,
                bangalore_office TEXT,
                website TEXT,
                careers_page TEXT,
                employee_count TEXT,
                industry TEXT,
                founded_year INTEGER,
                description TEXT,
                hiring_process TEXT,
                UNIQUE(name, city)
            )
        ''')

        # 9. company_skills table
        cursor.execute('DROP TABLE IF EXISTS company_skills')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                UNIQUE(company_name, skill_name)
            )
        ''')

        # 10. user_dream_company table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_dream_company (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                city TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 11. learning_resources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT UNIQUE NOT NULL,
                youtube_url TEXT NOT NULL,
                cert_url TEXT NOT NULL,
                practice_url TEXT NOT NULL
            )
        ''')

        # 12. saved_companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                city TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 13. application_tracker table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS application_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                city TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 14. placement_calendar table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS placement_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 15. coding_progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                problems_solved INTEGER NOT NULL,
                rating INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 16. recruiter_evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruiter_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                evaluator_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comments TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 17. readiness_scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readiness_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                overall_score INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 18. contact_messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()
        
        # Schema migration to add resolved column if needed
        try:
            cursor.execute("ALTER TABLE contact_messages ADD COLUMN resolved INTEGER DEFAULT 0")
            db.commit()
        except Exception:
            pass
        
        # Seed default users and jobs if database is empty
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            # Seed Admin
            admin_hashed = generate_password_hash("adminpassword", method='pbkdf2:sha256')
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                ("admin", "admin@placement.com", admin_hashed, 1)
            )
            
            # Seed Candidate
            student_hashed = generate_password_hash("Password123", method='pbkdf2:sha256')
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, cgpa, is_admin) VALUES (?, ?, ?, ?, ?)",
                ("john_developer", "john@example.com", student_hashed, 8.5, 0)
            )
            
            # Get Student user ID
            cursor.execute("SELECT id FROM users WHERE username = 'john_developer'")
            student_id = cursor.fetchone()['id']
            
            # Seed Student Skills
            cursor.executemany(
                "INSERT INTO skills (user_id, skill_name, proficiency) VALUES (?, ?, ?)",
                [
                    (student_id, "Python", "Advanced"),
                    (student_id, "SQL", "Intermediate"),
                    (student_id, "Git", "Intermediate")
                ]
            )
            
            # Seed Student Certifications
            cursor.execute(
                "INSERT INTO certifications (user_id, cert_name, issuing_org, issue_date) VALUES (?, ?, ?, ?)",
                (student_id, "AWS Cloud Practitioner", "Amazon Web Services", "06/2026")
            )
            
            # Seed Student Projects
            cursor.execute(
                "INSERT INTO projects (user_id, title, description, technologies) VALUES (?, ?, ?, ?)",
                (student_id, "AI Placement Assistant", "Designed a production-ready Flask career console.", "Python, Flask, SQLite")
            )
            
            # Seed Jobs
            cursor.executemany(
                "INSERT INTO jobs (title, company, description, requirements) VALUES (?, ?, ?, ?)",
                [
                    ("Junior Python Developer", "TechCorp Inc.", "Responsible for building backend endpoints and structure SQLite relational schemas.", "Python, SQL, Git"),
                    ("React Interface Developer", "WebCraft Solutions", "Design and coordinate responsive user interfaces using HTML, CSS, JavaScript, and React.", "JavaScript, HTML, CSS, React"),
                    ("Junior Data Analyst", "DataHub Corp", "Extract data using query syntax and compile analytics dashboards using Python.", "Python, SQL")
                ]
            )
            
            # Seed Placement Calendar Events
            cursor.executemany(
                "INSERT INTO placement_calendar (user_id, event_title, event_date, event_description) VALUES (?, ?, ?, ?)",
                [
                    (student_id, "Google Technical Interview Mock", "2026-07-15", "Focus on advanced algorithms, graphs and heaps"),
                    (student_id, "Microsoft Coding Assessment", "2026-07-22", "Online test containing 3 hard coding challenges"),
                    (student_id, "Accenture Interview Mock", "2026-08-01", "Verbal reasoning and core computer network structures")
                ]
            )

            # Seed Coding Progress Tracker
            cursor.executemany(
                "INSERT INTO coding_progress (user_id, platform, problems_solved, rating) VALUES (?, ?, ?, ?)",
                [
                    (student_id, "LeetCode", 240, 1780),
                    (student_id, "HackerRank", 150, 4),
                    (student_id, "GeeksforGeeks", 95, 1550)
                ]
            )

            # Seed Recruiter Evaluations
            cursor.executemany(
                "INSERT INTO recruiter_evaluations (user_id, company_name, evaluator_name, rating, comments) VALUES (?, ?, ?, ?, ?)",
                [
                    (student_id, "Google", "Lead Architect", 5, "Strong analytical approach, good at database optimization"),
                    (student_id, "Infosys", "Senior HR Partner", 4, "Excellent verbal articulation and clear project communication")
                ]
            )

            # Seed Readiness Scores History
            cursor.executemany(
                "INSERT INTO readiness_scores (user_id, overall_score, updated_at) VALUES (?, ?, ?)",
                [
                    (student_id, 55, "2026-06-10 09:00:00"),
                    (student_id, 64, "2026-06-20 09:00:00"),
                    (student_id, 72, "2026-06-30 09:00:00")
                ]
            )

            db.commit()

        # Seed companies and company skills by loading from companies_seed.json
        import os
        import json
        seed_path = os.path.join(os.path.dirname(__file__), 'companies_seed.json')
        if os.path.exists(seed_path):
            with open(seed_path, 'r') as f:
                COMPANIES_REGISTRY = json.load(f)
        else:
            COMPANIES_REGISTRY = []

        for comp in COMPANIES_REGISTRY:
            for city in comp["cities"]:
                pkg = comp.get("package_range", "5-12 LPA")
                logo_url = comp.get("logo_url", "")
                hq = comp.get("hq", "")
                blr_office = comp.get("bangalore_office", "")
                website = comp.get("website", "")
                careers_page = comp.get("careers_page", "")
                emp_count = comp.get("employee_count", "")
                industry = comp.get("industry", "")
                founded_year = comp.get("founded_year", None)
                description = comp.get("description", "")
                hiring_process = comp.get("hiring_process", "")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO companies (
                        name, city, type, branches, min_cgpa, tech_skills, soft_skills, 
                        pref_certs, pref_projects, hiring_roles, package_range,
                        logo_url, hq, bangalore_office, website, careers_page,
                        employee_count, industry, founded_year, description, hiring_process
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comp["name"], city, comp["type"], comp["branches"], comp["min_cgpa"],
                    comp["tech_skills"], comp["soft_skills"], comp["pref_certs"], comp["pref_projects"],
                    comp["hiring_roles"], pkg, logo_url, hq, blr_office, website, careers_page,
                    emp_count, industry, founded_year, description, hiring_process
                ))
                
                # Dynamic populate company_skills for backward compatibility
                all_skills = [s.strip() for s in comp["tech_skills"].split(",") if s.strip()] + [s.strip() for s in comp["soft_skills"].split(",") if s.strip()]
                for s in all_skills:
                    cursor.execute('''
                        INSERT OR IGNORE INTO company_skills (company_name, skill_name) VALUES (?, ?)
                    ''', (comp["name"], s))
        db.commit()

        cursor.execute("SELECT COUNT(*) as count FROM learning_resources")
        if cursor.fetchone()['count'] == 0:
            resources_data = [
                ("DSA", "https://www.youtube.com/embed/videoseries?list=PL2_aWCzGMAwI3W_AddKK586yQrSCJH1Kf", "https://www.hackerrank.com/certificates/verify/dsa", "https://leetcode.com/problemset/all/"),
                ("Python", "https://www.youtube.com/embed/rfscVS0vtbw", "https://www.pythoninstitute.org/pcep", "https://www.hackerrank.com/domains/python"),
                ("Java", "https://www.youtube.com/embed/A74TOXlaTFM", "https://education.oracle.com/oracle-certified-professional-java-se-11-developer/pexam_1Z0-819", "https://www.hackerrank.com/domains/java"),
                ("SQL", "https://www.youtube.com/embed/HXV3zeQKqGY", "https://www.hackerrank.com/certificates/verify/sql", "https://www.hackerrank.com/domains/sql"),
                ("Git", "https://www.youtube.com/embed/RGOj5yH7evk", "https://www.freecodecamp.org/news/git-and-github-certification-course/", "https://github.com"),
                ("System Design", "https://www.youtube.com/embed/m8IOfR6hIP0", "https://www.educative.co/courses/grokking-modern-system-design-interview", "https://github.com/donnemartin/system-design-primer"),
                ("Problem Solving", "https://www.youtube.com/embed/videoseries?list=PLgUwDviBIf0oF6QL8m24FCgCabLtCXUpO", "https://www.hackerrank.com/certificates/verify/problem-solving", "https://www.hackerrank.com/domains/algorithms"),
                ("AWS", "https://www.youtube.com/embed/3hLmDS179YE", "https://aws.amazon.com/certification/certified-cloud-practitioner/", "https://aws.amazon.com/free/"),
                ("OOP", "https://www.youtube.com/embed/SiBw7osapzI", "https://www.udemy.com/course/oop-java-object-oriented-programming-in-java/", "https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/"),
                ("Aptitude", "https://www.youtube.com/embed/videoseries?list=PLpyc33gOfe4A_V8EIsfXjHl4V29Z19XN-", "https://www.indiabix.com/", "https://www.indiabix.com/aptitude/questions-and-answers/"),
                ("Communication Skills", "https://www.youtube.com/embed/HAnw168huqA", "https://www.coursera.org/specializations/improve-english", "https://www.toastmasters.org/"),
                ("JavaScript", "https://www.youtube.com/embed/PkZNo7MFNFg", "https://www.freecodecamp.org/certification/javascript-algorithms-and-data-structures-v8", "https://www.codewars.com/"),
                ("HTML", "https://www.youtube.com/embed/ok-plXXHlWw", "https://www.freecodecamp.org/certification/responsive-web-design", "https://www.w3schools.com/html/"),
                ("CSS", "https://www.youtube.com/embed/1Rs2ND1ryYc", "https://www.freecodecamp.org/certification/responsive-web-design", "https://css-tricks.com/"),
                ("C++", "https://www.youtube.com/embed/vLnPwxZdW4Y", "https://cppinstitute.org/c-certified-associate-programmer", "https://leetcode.com/problemset/all/?languageTags=cpp"),
                ("C#", "https://www.youtube.com/embed/gfkTfcpWqAY", "https://learn.microsoft.com/en-us/credentials/certifications/csharp-developer/", "https://www.hackerrank.com/domains/csharp"),
                ("C", "https://www.youtube.com/embed/KJgsSF0S9DU", "https://cppinstitute.org/cla-c-programming-language-certified-associate", "https://www.hackerrank.com/domains/c"),
                ("Networking", "https://www.youtube.com/embed/IPvYjXCsTg8", "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html", "https://www.packettracernetwork.com/"),
                ("Excel", "https://www.youtube.com/embed/rwbho0CgEAE", "https://learn.microsoft.com/en-us/credentials/certifications/microsoft-office-specialist-excel-associate/", "https://www.excelexposure.com/"),
                ("Analytics", "https://www.youtube.com/embed/videoseries?list=PLUaB-1hjhk8FE_XZ87vPPSfHqbVkcJLK6", "https://grow.google/certificates/data-analytics/", "https://www.kaggle.com/"),
                ("Electronics", "https://www.youtube.com/embed/videoseries?list=PLm_MSClsnwm8Hja56A5uL3sNlqf3lJv6o", "https://www.edx.org/learn/electronics", "https://www.multisim.com/"),
                ("QA", "https://www.youtube.com/embed/s3R2S39h2m0", "https://www.istqb.org/certifications/certified-tester-foundation-level", "https://www.ministryoftesting.com/"),
                ("Ruby", "https://www.youtube.com/embed/t_ispmWqvjY", "https://www.freecodecamp.org/news/learn-ruby-programming-complete-course/", "https://www.hackerrank.com/domains/ruby"),
                ("Go", "https://www.youtube.com/embed/YS4e4q9oBaU", "https://www.freecodecamp.org/news/learn-go-programming-complete-course/", "https://exercism.org/tracks/go"),
                ("Management", "https://www.youtube.com/embed/Pj13k8G1T_s", "https://www.coursera.org/specializations/project-management", "https://www.pmi.org/certifications/project-management-pmp"),
                ("Spring Boot", "https://www.youtube.com/embed/35EQXmHKZYs", "https://www.udemy.com/course/spring-boot-3-spring-6-framework-for-beginners/", "https://spring.io/guides")
            ]
            cursor.executemany(
                "INSERT OR IGNORE INTO learning_resources (skill_name, youtube_url, cert_url, practice_url) VALUES (?, ?, ?, ?)",
                resources_data
            )
            db.commit()

# Run database initialization
init_db()

# -------------------------------------------------------------
# Security Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the administrator panel.', 'warning')
            return redirect(url_for('login'))
        # Check database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or not user['is_admin']:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper for PDF parser
def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error during PDF text extraction: {e}")
        return ""

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------------------------------------------------
# Core Authorization Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    
    # Fetch a few featured companies for recommendations
    cursor.execute("""
        SELECT name, logo_url AS logo, type AS category, package_range, city AS location 
        FROM companies 
        WHERE name IN ('Google', 'Microsoft', 'Amazon', 'Adobe', 'Infosys', 'TCS', 'Wipro', 'Accenture') AND city = 'Bangalore' 
        ORDER BY CASE name 
            WHEN 'Google' THEN 1 
            WHEN 'Microsoft' THEN 2 
            WHEN 'Amazon' THEN 3 
            WHEN 'Adobe' THEN 4 
            WHEN 'Infosys' THEN 5 
            WHEN 'TCS' THEN 6 
            WHEN 'Wipro' THEN 7 
            WHEN 'Accenture' THEN 8 
        END
    """)
    featured_companies = cursor.fetchall()
    
    user = None
    if 'user_id' in session:
        cursor.execute("SELECT username, email, branch, cgpa FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        
    return render_template('index.html', featured_companies=featured_companies, user=user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        gender = request.form.get('gender', '').strip()
        
        if not username or not email or not password or not gender:
            flash('All credentials and gender are required.', 'danger')
            return render_template('signup.html')
            
        if gender not in ['Male', 'Female', 'Prefer not to say']:
            flash('Invalid gender selection.', 'danger')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('Username or email already registered.', 'danger')
            return render_template('signup.html')
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, gender) VALUES (?, ?, ?, ?)',
                (username, email, hashed_pw, gender)
            )
            db.commit()
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            session['user_id'] = user['id']
            session['username'] = username
            flash('Account created successfully! Welcome to your Dashboard.', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'An database error occurred: {str(e)}', 'danger')
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username/email and password.', 'danger')
            return render_template('login.html')
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Logged in successfully. Welcome back, {user["username"]}!', 'success')
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------------------------------------
# Student Dashboard Routes
# -------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    # 1. Fetch user core info (check if admin, redirect appropriately)
    cursor.execute('SELECT is_admin, username, email, cgpa, branch, gender, profile_picture FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user and user['is_admin']:
        return redirect(url_for('admin_dashboard'))
        
    if user:
        user = dict(user)
        if user.get('profile_picture'):
            user['profile_picture_url'] = url_for('uploaded_file', filename=user['profile_picture'])
        else:
            if user.get('gender') == 'Female':
                user['profile_picture_url'] = url_for('static', filename='images/default_female.svg')
            elif user.get('gender') == 'Prefer not to say':
                user['profile_picture_url'] = url_for('static', filename='images/default_neutral.svg')
            else:
                user['profile_picture_url'] = url_for('static', filename='images/default_male.svg')
        
    # 2. Fetch lists
    cursor.execute('SELECT * FROM skills WHERE user_id = ?', (user_id,))
    skills = cursor.fetchall()
    
    frontend_names = {'html', 'css', 'javascript', 'js', 'bootstrap', 'react', 'tailwind css', 'tailwind', 'ui/ux design', 'ui/ux', 'ui design', 'ux design'}
    backend_names = {'python', 'flask', 'java', 'mysql', 'sqlite', 'node.js', 'nodejs', 'node', 'rest apis', 'rest api', 'restful apis', 'restful api', 'api'}
    
    frontend_skills = []
    backend_skills = []
    other_skills = []
    
    for s in skills:
        s_name = s['skill_name'].lower().strip()
        if s_name in frontend_names or any(f == s_name or s_name.startswith(f) or s_name.endswith(f) for f in frontend_names):
            frontend_skills.append(s)
        elif s_name in backend_names or any(b == s_name or s_name.startswith(b) or s_name.endswith(b) for b in backend_names):
            backend_skills.append(s)
        else:
            other_skills.append(s)
            
    frontend_skills_count = len(frontend_skills)
    backend_skills_count = len(backend_skills)
    
    cursor.execute('SELECT * FROM certifications WHERE user_id = ?', (user_id,))
    certifications = cursor.fetchall()
    
    cursor.execute('SELECT * FROM projects WHERE user_id = ?', (user_id,))
    projects = cursor.fetchall()
    
    cursor.execute('SELECT * FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
    latest_resume = cursor.fetchone()

    cursor.execute('SELECT * FROM user_dream_company WHERE user_id = ?', (user_id,))
    dream_company = cursor.fetchone()
    
    # Calculate readiness score and metrics if dream company is selected
    readiness_score = None
    missing_skills_count = None
    ready_skills_count = None
    recommended_certs = None
    placement_prob = None
    if dream_company:
        cursor.execute('SELECT * FROM companies WHERE name = ? AND city = ?', (dream_company['company_name'], dream_company['city']))
        comp_info = cursor.fetchone()
        if not comp_info:
            cursor.execute('SELECT * FROM companies WHERE name = ? LIMIT 1', (dream_company['company_name'],))
            comp_info = cursor.fetchone()
            
        if comp_info:
            req_tech = [s.strip() for s in comp_info['tech_skills'].split(',') if s.strip()]
            req_soft = [s.strip() for s in comp_info['soft_skills'].split(',') if s.strip()]
            all_req_skills = req_tech + req_soft
            
            cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
            user_skills = {row['skill_name'].lower().strip() for row in cursor.fetchall()}
            
            matched_count = 0
            missing_count = 0
            for s in all_req_skills:
                if s.lower().strip() in user_skills:
                    matched_count += 1
                else:
                    missing_count += 1
                    
            if len(all_req_skills) > 0:
                readiness_score = int((matched_count / len(all_req_skills)) * 100)
            else:
                readiness_score = 0
                
            ready_skills_count = matched_count
            missing_skills_count = missing_count
            
            # Recommended certifications
            cursor.execute('SELECT cert_name FROM certifications WHERE user_id = ?', (user_id,))
            user_certs = [row['cert_name'].lower().strip() for row in cursor.fetchall()]
            pref_certs = [c.strip() for c in comp_info['pref_certs'].split(',') if c.strip()]
            
            missing_c = []
            for pc in pref_certs:
                matched = False
                for uc in user_certs:
                    if pc.lower().strip() in uc or uc in pc.lower().strip():
                        matched = True
                        break
                if not matched:
                    missing_c.append(pc)
            recommended_certs = ", ".join(missing_c) if missing_c else "None"
            
            # Placement probability estimation
            user_cgpa = user['cgpa'] if user['cgpa'] is not None else 0.0
            cursor.execute('SELECT ats_score FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
            res_row = cursor.fetchone()
            ats_score = res_row['ats_score'] if res_row else 70.0
            
            cgpa_contrib = (user_cgpa / 10.0) * 100.0
            placement_prob = int(0.5 * readiness_score + 0.3 * cgpa_contrib + 0.2 * ats_score)
            placement_prob = min(99, max(10, placement_prob))
        
    return render_template(
        'dashboard.html',
        user=user,
        skills=skills,
        frontend_skills=frontend_skills,
        backend_skills=backend_skills,
        other_skills=other_skills,
        frontend_skills_count=frontend_skills_count,
        backend_skills_count=backend_skills_count,
        certifications=certifications,
        projects=projects,
        latest_resume=latest_resume,
        dream_company=dream_company,
        readiness_score=readiness_score,
        missing_skills_count=missing_skills_count,
        ready_skills_count=ready_skills_count,
        recommended_certs=recommended_certs,
        placement_prob=placement_prob
    )

# Student Settings updates
@app.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    cgpa = request.form.get('cgpa', None)
    branch = request.form.get('branch', None)
    
    if cgpa is None or cgpa == '':
        return jsonify({'success': False, 'message': 'CGPA field is empty.'}), 400
    try:
        cgpa_val = float(cgpa)
        if not (0.0 <= cgpa_val <= 10.0):
            return jsonify({'success': False, 'message': 'CGPA must be between 0.0 and 10.0 (Indian grading scale).'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid CGPA format. Please enter a number between 0.0 and 10.0.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET cgpa = ?, branch = ? WHERE id = ?', (cgpa_val, branch, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully.'})

# Profile Picture APIs
@app.route('/api/upload-profile-pic', methods=['POST'])
@login_required
def upload_profile_pic():
    file = request.files.get('profile_picture')
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400
    
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']:
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF, WEBP, SVG.'}), 400
        
    filename = secure_filename(f"profile_{session['user_id']}.{ext}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET profile_picture = ? WHERE id = ?', (filename, session['user_id']))
    db.commit()
    
    profile_picture_url = url_for('uploaded_file', filename=filename)
    return jsonify({
        'success': True, 
        'message': 'Profile picture updated successfully.',
        'profile_picture_url': profile_picture_url
    })

@app.route('/api/remove-profile-pic', methods=['POST'])
@login_required
def remove_profile_pic():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT gender, profile_picture FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Optionally delete the file from filesystem if it exists
    if user and user['profile_picture']:
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user['profile_picture'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing profile picture file: {e}")

    cursor.execute('UPDATE users SET profile_picture = NULL WHERE id = ?', (session['user_id'],))
    db.commit()
    
    gender = user['gender'] if user else 'Male'
    if gender == 'Female':
        default_avatar_url = url_for('static', filename='images/default_female.svg')
    elif gender == 'Prefer not to say':
        default_avatar_url = url_for('static', filename='images/default_neutral.svg')
    else:
        default_avatar_url = url_for('static', filename='images/default_male.svg')
        
    return jsonify({
        'success': True,
        'message': 'Profile picture removed successfully.',
        'profile_picture_url': default_avatar_url
    })

# Skills APIs
@app.route('/api/add-skill', methods=['POST'])
@login_required
def add_skill():
    skill_name = request.form.get('skill_name', '').strip()
    proficiency = request.form.get('proficiency', '').strip()
    if not skill_name or not proficiency:
        return jsonify({'success': False, 'message': 'Skill credentials required.'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM skills WHERE user_id = ? AND LOWER(skill_name) = ?', (session['user_id'], skill_name.lower()))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Skill already exists in your profile.'}), 400
        
    cursor.execute('INSERT INTO skills (user_id, skill_name, proficiency) VALUES (?, ?, ?)', (session['user_id'], skill_name, proficiency))
    db.commit()
    return jsonify({'success': True, 'message': 'Skill added.'})

@app.route('/api/delete-skill', methods=['POST'])
@login_required
def delete_skill():
    skill_id = request.form.get('skill_id', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM skills WHERE id = ? AND user_id = ?', (skill_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Skill deleted.'})

# Certifications APIs
@app.route('/api/add-certification', methods=['POST'])
@login_required
def add_certification():
    cert_name = request.form.get('cert_name', '').strip()
    issuing_org = request.form.get('issuing_org', '').strip()
    issue_date = request.form.get('issue_date', '').strip()
    if not cert_name:
        return jsonify({'success': False, 'message': 'Certification title required.'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO certifications (user_id, cert_name, issuing_org, issue_date) VALUES (?, ?, ?, ?)', (session['user_id'], cert_name, issuing_org, issue_date))
    db.commit()
    return jsonify({'success': True, 'message': 'Certification added.'})

@app.route('/api/delete-certification', methods=['POST'])
@login_required
def delete_certification():
    cert_id = request.form.get('cert_id', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM certifications WHERE id = ? AND user_id = ?', (cert_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Certification deleted.'})

# Projects APIs
@app.route('/api/add-project', methods=['POST'])
@login_required
def add_project():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    technologies = request.form.get('technologies', '').strip()
    if not title:
        return jsonify({'success': False, 'message': 'Project title required.'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO projects (user_id, title, description, technologies) VALUES (?, ?, ?, ?)', (session['user_id'], title, description, technologies))
    db.commit()
    return jsonify({'success': True, 'message': 'Project added.'})

@app.route('/api/delete-project', methods=['POST'])
@login_required
def delete_project():
    project_id = request.form.get('project_id', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM projects WHERE id = ? AND user_id = ?', (project_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Project deleted.'})

# -------------------------------------------------------------
# Complete Placement Portal Modules APIs (SQLite-backed CRUD)
# -------------------------------------------------------------

# 1. Saved Companies APIs
@app.route('/api/saved-companies', methods=['GET'])
@login_required
def get_saved_companies():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT s.id, s.company_name, s.city, c.package_range 
        FROM saved_companies s 
        LEFT JOIN companies c ON LOWER(s.company_name) = LOWER(c.name) AND LOWER(s.city) = LOWER(c.city) 
        WHERE s.user_id = ?
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    companies = [{
        'id': r['id'], 
        'name': r['company_name'], 
        'city': r['city'], 
        'package_range': r['package_range'] if r['package_range'] else '5-12 LPA'
    } for r in rows]
    return jsonify({'success': True, 'companies': companies})

@app.route('/api/saved-companies/add', methods=['POST'])
@login_required
def add_saved_company():
    company_name = request.form.get('company_name', '').strip()
    city = request.form.get('city', '').strip()
    if not company_name or not city:
        return jsonify({'success': False, 'message': 'Company credentials required.'}), 400
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id FROM saved_companies WHERE user_id = ? AND LOWER(company_name) = ? AND LOWER(city) = ?', 
                   (session['user_id'], company_name.lower(), city.lower()))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Company already saved.'}), 400
        
    cursor.execute('INSERT INTO saved_companies (user_id, company_name, city) VALUES (?, ?, ?)', (session['user_id'], company_name, city))
    db.commit()
    return jsonify({'success': True, 'message': f'{company_name} saved.'})

@app.route('/api/saved-companies/delete', methods=['POST'])
@login_required
def delete_saved_company():
    company_name = request.form.get('company_name', '').strip()
    city = request.form.get('city', '').strip()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM saved_companies WHERE user_id = ? AND LOWER(company_name) = ? AND LOWER(city) = ?', 
                   (session['user_id'], company_name.lower(), city.lower()))
    db.commit()
    return jsonify({'success': True, 'message': 'Saved company deleted.'})


# 2. Application Tracker APIs
@app.route('/api/tracked-applications', methods=['GET'])
@login_required
def get_tracked_applications():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM application_tracker WHERE user_id = ?', (session['user_id'],))
    rows = cursor.fetchall()
    apps = [{'id': r['id'], 'name': r['company_name'], 'city': r['city'], 'type': r['type'], 'status': r['status']} for r in rows]
    return jsonify({'success': True, 'applications': apps})

@app.route('/api/tracked-applications/save', methods=['POST'])
@login_required
def save_tracked_application():
    company_name = request.form.get('company_name', '').strip()
    city = request.form.get('city', '').strip()
    type_val = request.form.get('type', 'Product Based').strip()
    status = request.form.get('status', 'Applied').strip()
    
    if not company_name or not city or not status:
        return jsonify({'success': False, 'message': 'Incomplete application tracking fields.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id FROM application_tracker WHERE user_id = ? AND LOWER(company_name) = ? AND LOWER(city) = ?', 
                   (session['user_id'], company_name.lower(), city.lower()))
    exist = cursor.fetchone()
    if exist:
        cursor.execute('UPDATE application_tracker SET status = ? WHERE id = ?', (status, exist['id']))
    else:
        cursor.execute('INSERT INTO application_tracker (user_id, company_name, city, type, status) VALUES (?, ?, ?, ?, ?)', 
                       (session['user_id'], company_name, city, type_val, status))
    db.commit()
    return jsonify({'success': True, 'message': 'Application tracking status saved.'})

@app.route('/api/tracked-applications/delete', methods=['POST'])
@login_required
def delete_tracked_application():
    company_name = request.form.get('company_name', '').strip()
    city = request.form.get('city', '').strip()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM application_tracker WHERE user_id = ? AND LOWER(company_name) = ? AND LOWER(city) = ?', 
                   (session['user_id'], company_name.lower(), city.lower()))
    db.commit()
    return jsonify({'success': True, 'message': 'Application deleted from tracker.'})


# 3. Placement Calendar APIs
@app.route('/api/calendar-events', methods=['GET'])
@login_required
def get_calendar_events():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM placement_calendar WHERE user_id = ? ORDER BY event_date ASC', (session['user_id'],))
    rows = cursor.fetchall()
    events = [{'id': r['id'], 'title': r['event_title'], 'date': r['event_date'], 'description': r['event_description']} for r in rows]
    return jsonify({'success': True, 'events': events})

@app.route('/api/calendar-events/add', methods=['POST'])
@login_required
def add_calendar_event():
    title = request.form.get('title', '').strip()
    date_val = request.form.get('date', '').strip()
    description = request.form.get('description', '').strip()
    
    if not title or not date_val:
        return jsonify({'success': False, 'message': 'Event title and date required.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO placement_calendar (user_id, event_title, event_date, event_description) VALUES (?, ?, ?, ?)', 
                   (session['user_id'], title, date_val, description))
    db.commit()
    return jsonify({'success': True, 'message': 'Calendar event scheduled.'})

@app.route('/api/calendar-events/delete', methods=['POST'])
@login_required
def delete_calendar_event():
    event_id = request.form.get('event_id', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM placement_calendar WHERE id = ? AND user_id = ?', (event_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Calendar event deleted.'})


# 4. Coding Progress Tracker APIs
@app.route('/api/coding-progress', methods=['GET'])
@login_required
def get_coding_progress():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM coding_progress WHERE user_id = ?', (session['user_id'],))
    rows = cursor.fetchall()
    progress = [{'id': r['id'], 'platform': r['platform'], 'problems_solved': r['problems_solved'], 'rating': r['rating']} for r in rows]
    return jsonify({'success': True, 'progress': progress})

@app.route('/api/coding-progress/save', methods=['POST'])
@login_required
def save_coding_progress():
    platform = request.form.get('platform', '').strip()
    problems = request.form.get('problems_solved', '').strip()
    rating = request.form.get('rating', '').strip()
    
    if not platform or not problems:
        return jsonify({'success': False, 'message': 'Platform and solved count required.'}), 400
        
    try:
        problems_val = int(problems)
        rating_val = int(rating) if rating else None
    except ValueError:
        return jsonify({'success': False, 'message': 'Values must be numeric.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id FROM coding_progress WHERE user_id = ? AND LOWER(platform) = ?', 
                   (session['user_id'], platform.lower()))
    exist = cursor.fetchone()
    if exist:
        cursor.execute('UPDATE coding_progress SET problems_solved = ?, rating = ? WHERE id = ?', (problems_val, rating_val, exist['id']))
    else:
        cursor.execute('INSERT INTO coding_progress (user_id, platform, problems_solved, rating) VALUES (?, ?, ?, ?)', 
                       (session['user_id'], platform, problems_val, rating_val))
    db.commit()
    return jsonify({'success': True, 'message': 'Coding metrics updated.'})

@app.route('/api/coding-progress/delete', methods=['POST'])
@login_required
def delete_coding_progress():
    progress_id = request.form.get('progress_id', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM coding_progress WHERE id = ? AND user_id = ?', (progress_id, session['user_id']))
    db.commit()
    return jsonify({'success': True, 'message': 'Coding entry deleted.'})


# 5. Recruiter Evaluations APIs
@app.route('/api/recruiter-evaluations', methods=['GET'])
@login_required
def get_recruiter_evaluations():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM recruiter_evaluations WHERE user_id = ?', (session['user_id'],))
    rows = cursor.fetchall()
    evals = [{'id': r['id'], 'company': r['company_name'], 'evaluator': r['evaluator_name'], 'rating': r['rating'], 'comments': r['comments']} for r in rows]
    return jsonify({'success': True, 'evaluations': evals})

@app.route('/api/recruiter-evaluations/add', methods=['POST'])
@login_required
def add_recruiter_evaluation():
    company = request.form.get('company_name', '').strip()
    evaluator = request.form.get('evaluator_name', '').strip()
    rating = request.form.get('rating', '').strip()
    comments = request.form.get('comments', '').strip()
    
    if not company or not evaluator or not rating:
        return jsonify({'success': False, 'message': 'Company, evaluator, and score required.'}), 400
        
    try:
        rating_val = int(rating)
        if not (1 <= rating_val <= 5):
            return jsonify({'success': False, 'message': 'Rating must be 1 to 5.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Rating must be a number.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO recruiter_evaluations (user_id, company_name, evaluator_name, rating, comments) VALUES (?, ?, ?, ?, ?)', 
                   (session['user_id'], company, evaluator, rating_val, comments))
    db.commit()
    return jsonify({'success': True, 'message': 'Recruiter evaluation added.'})


# 6. Placement Readiness Score History APIs
@app.route('/api/readiness-scores', methods=['GET'])
@login_required
def get_readiness_scores():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM readiness_scores WHERE user_id = ? ORDER BY updated_at ASC', (session['user_id'],))
    rows = cursor.fetchall()
    scores = [{'overall_score': r['overall_score'], 'updated_at': r['updated_at']} for r in rows]
    return jsonify({'success': True, 'scores': scores})

# -------------------------------------------------------------
# Upgraded ATS & Resume Analyzer API
# -------------------------------------------------------------
@app.route('/api/analyze-resume', methods=['POST'])
@login_required
def analyze_resume():
    if 'resume_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
        
    file = request.files['resume_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Selected file is empty.'}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filename_unique = f"{session['user_id']}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_unique)
        file.save(filepath)
        
        # Parse PDF text
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            return jsonify({'success': False, 'message': 'Unable to extract text from PDF.'}), 400
            
        tech_catalog = {
            'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java', 'sql': 'SQL', 
            'react': 'React', 'flask': 'Flask', 'django': 'Django', 'html': 'HTML', 
            'css': 'CSS', 'bootstrap': 'Bootstrap', 'aws': 'AWS', 'docker': 'Docker', 
            'git': 'Git', 'kubernetes': 'Kubernetes', 'node.js': 'Node.js', 
            'typescript': 'TypeScript', 'mongodb': 'MongoDB', 'postgresql': 'PostgreSQL', 
            'c++': 'C++', 'machine learning': 'Machine Learning', 'data science': 'Data Science'
        }
        
        detected_skills = []
        text_lower = text.lower()
        for key, display_val in tech_catalog.items():
            if key in text_lower:
                detected_skills.append(display_val)
                
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (session['user_id'],))
        profile_skills = [row['skill_name'] for row in cursor.fetchall()]
        
        missing_skills = []
        for p_skill in profile_skills:
            if p_skill.lower() not in text_lower:
                missing_skills.append(p_skill)
                
        # Seed 3 recommendations if not found
        rec_added = 0
        for key, display_val in tech_catalog.items():
            if rec_added >= 3:
                break
            if key not in text_lower and display_val not in missing_skills and display_val not in profile_skills:
                missing_skills.append(display_val)
                rec_added += 1
                
        # Score computation
        words_len = len(text.split())
        density_score = min(20, int(words_len / 15))
        
        sections_score = 0
        for heading in ['experience', 'education', 'projects', 'skills']:
            if heading in text_lower:
                sections_score += 10
                
        keyword_score = min(40, len(detected_skills) * 8)
        ats_score = density_score + sections_score + keyword_score
        
        feedback = []
        if words_len < 180:
            feedback.append("Resume contains low word count. Expand project descriptions using the STAR method.")
        if sections_score < 40:
            feedback.append("Structure checklist failed: missing key headings. Ensure 'Education', 'Experience', 'Projects', and 'Skills' are clearly defined.")
        if len(detected_skills) < 4:
            feedback.append("Keyword density is low. Integrate additional framework keywords and programming languages.")
        if ats_score >= 80:
            feedback.append("Strong ATS matches detected. Polish spelling alignment and quantify your project impacts (e.g. 'boosted performance by 25%').")
            
        cursor.execute(
            'INSERT INTO resumes (user_id, filename, extracted_text, ats_score) VALUES (?, ?, ?, ?)',
            (session['user_id'], filename, text, ats_score)
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'ats_score': ats_score,
            'skills_detected': detected_skills,
            'missing_skills': missing_skills,
            'feedback': feedback
        })
        
    return jsonify({'success': False, 'message': 'Invalid file format. Only PDF uploads are supported.'}), 400

# -------------------------------------------------------------
# Placement Predictor Endpoint
# -------------------------------------------------------------
@app.route('/api/predict-placement', methods=['POST'])
@login_required
def predict_placement():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    cursor.execute('SELECT cgpa FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or user['cgpa'] is None:
        return jsonify({'success': False, 'message': 'Profile setup is incomplete. Please enter your CGPA in the profile section first.'}), 400
        
    cgpa = user['cgpa']
    
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    skills = [row['skill_name'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT title FROM projects WHERE user_id = ?', (user_id,))
    projects = [row['title'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT cert_name FROM certifications WHERE user_id = ?', (user_id,))
    certs = [row['cert_name'] for row in cursor.fetchall()]
    
    prob = 35.0
    cgpa_contrib = (cgpa / 10.0) * 30.0   # Indian CGPA scale: 0–10
    prob += cgpa_contrib
    
    skills_contrib = min(15.0, len(skills) * 3.0)
    prob += skills_contrib
    
    projects_contrib = min(12.0, len(projects) * 6.0)
    prob += projects_contrib
    
    certs_contrib = min(8.0, len(certs) * 4.0)
    prob += certs_contrib
    
    final_prob = min(99.0, round(prob, 1))
    
    recommendations = []
    if cgpa < 7.0:
        recommendations.append("Your CGPA is below 7.0/10. Prioritize academic performance or compensate with strong projects, certifications, and internships.")
    if len(skills) < 4:
        recommendations.append("Expand your toolkit. Register at least 4 core technical skills on your dashboard (e.g. databases, programming languages).")
    if len(projects) < 2:
        recommendations.append("Develop and list at least 2 structured projects showing backend/frontend tools integration.")
    if len(certs) < 1:
        recommendations.append("Earn professional certifications (e.g., AWS Cloud Practitioner, Java Associate) to validate your profile credentials.")
    if final_prob >= 85.0:
        recommendations.append("Outstanding profile! You have a high probability of placement. Start practicing mock coding tests and behavioral interviews.")
    elif 65.0 <= final_prob < 85.0:
        recommendations.append("Good likelihood. Enhance your resume keywords match score to easily pass preliminary ATS filters.")
        
    return jsonify({
        'success': True,
        'probability': final_prob,
        'recommendations': recommendations,
        'stats': {
            'cgpa_contrib': round(cgpa_contrib, 1),
            'skills_contrib': round(skills_contrib, 1),
            'projects_contrib': round(projects_contrib, 1),
            'certs_contrib': round(certs_contrib, 1)
        }
    })

# AI-Powered Career Intelligence Console API
@app.route('/api/ai-career-intelligence/data', methods=['GET'])
@login_required
def get_ai_career_intelligence_data():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    # 1. Fetch user profile
    cursor.execute('SELECT username, email, cgpa, branch, gender FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'User profile not found.'}), 404
        
    cgpa = user['cgpa'] if user['cgpa'] is not None else 0.0
    
    # 2. Fetch logged skills, projects, certifications
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    skills = [row['skill_name'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT title, technologies, description FROM projects WHERE user_id = ?', (user_id,))
    projects = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT cert_name, issuing_org FROM certifications WHERE user_id = ?', (user_id,))
    certs = [dict(row) for row in cursor.fetchall()]
    
    # 3. Fetch latest resume
    cursor.execute('SELECT id, filename, ats_score, extracted_text FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
    latest_resume = cursor.fetchone()
    
    ats_score = latest_resume['ats_score'] if latest_resume else 0
    resume_text = latest_resume['extracted_text'] if latest_resume else ""
    
    # 4. ATS & Resume Strength Analysis
    word_count = len(resume_text.split()) if resume_text else 0
    formatting_strength = 0
    keyword_density = 0
    section_completion = 0
    
    if latest_resume:
        formatting_strength = min(100, 60 + (ats_score // 5) + min(15, word_count // 30))
        keyword_density = min(100, len(skills) * 8 + (ats_score // 3))
        sections_found = sum(1 for sec in ['experience', 'education', 'projects', 'skills'] if sec in resume_text.lower())
        section_completion = 40 + sections_found * 15
    else:
        formatting_strength = 0
        keyword_density = 0
        section_completion = 0
        
    # Improvement suggestions
    suggestions = []
    if not latest_resume:
        suggestions.append("Upload a resume to analyze your layout parser compatibility.")
    else:
        if word_count < 180:
            suggestions.append("Increase descriptions density: include at least 180 words inside details columns.")
        if len(skills) < 4:
            suggestions.append("Integrate keyword matches: add key programming languages directly to your Skills header.")
        if formatting_strength < 75:
            suggestions.append("Avoid graphic boxes: clean complex layout layers to assist recruiter ATS scanners.")
        if len(suggestions) == 0:
            suggestions.append("Excellent layout. Add numeric metrics to highlight project deliverables.")
            
    # 5. Matching companies engine
    cursor.execute('SELECT * FROM companies LIMIT 6')
    companies_rows = cursor.fetchall()
    
    matching_companies = []
    for c in companies_rows:
        req_skills_raw = c['tech_skills'] if c['tech_skills'] else ''
        req_skills = [s.strip().lower() for s in req_skills_raw.split(',') if s.strip()]
        
        user_skills_lower = [s.lower() for s in skills]
        matched = [s for s in req_skills if s in user_skills_lower]
        missing = [s for s in req_skills if s not in user_skills_lower]
        
        base_match = 40.0
        if len(req_skills) > 0:
            base_match += (len(matched) / len(req_skills)) * 40.0
        
        company_min_cgpa = c['min_cgpa'] if c['min_cgpa'] is not None else 6.0
        if cgpa >= company_min_cgpa:
            base_match += 15.0
        else:
            base_match += 5.0
            
        if len(projects) > 0:
            base_match += min(5.0, len(projects) * 2.0)
            
        match_percentage = min(99.0, round(base_match, 1))
        
        eligible = True
        reasons = []
        if cgpa < company_min_cgpa:
            eligible = False
            reasons.append(f"CGPA score below company minimum threshold ({company_min_cgpa})")
        if len(missing) > 2:
            eligible = False
            reasons.append(f"Missing tech stacks: {', '.join(missing[:2])}")
            
        matching_companies.append({
            'name': c['name'],
            'logo': c['logo_url'] if c['logo_url'] else 'default_logo.svg',
            'category': c['type'],
            'package': c['package_range'],
            'match_percent': match_percentage,
            'eligible': eligible,
            'reasons': reasons,
            'skills_compare': {
                'matched': [s.title() for s in matched],
                'missing': [s.title() for s in missing]
            }
        })
        
    matching_companies.sort(key=lambda x: x['match_percent'], reverse=True)
    
    # 6. Placement Readiness & Success Odds
    prob = 35.0
    cgpa_contrib = (cgpa / 10.0) * 30.0
    prob += cgpa_contrib
    skills_contrib = min(15.0, len(skills) * 3.0)
    prob += skills_contrib
    projects_contrib = min(12.0, len(projects) * 6.0)
    prob += projects_contrib
    certs_contrib = min(8.0, len(certs) * 4.0)
    prob += certs_contrib
    
    final_prob = min(99.0, round(prob, 1))
    
    # 7. AI Recommendations
    courses = []
    recommended_certs = []
    recommended_projects = []
    
    user_skills_lower = [s.lower() for s in skills]
    if 'python' not in user_skills_lower:
        courses.append({'title': 'Complete Python Bootcamp From Zero to Hero', 'platform': 'Udemy'})
        recommended_projects.append({'title': 'Algorithmic Trading Bot in Python', 'tech': 'Python, API calls'})
    if 'react' not in user_skills_lower:
        courses.append({'title': 'React - The Complete Guide (incl. React Router)', 'platform': 'Udemy'})
        recommended_projects.append({'title': 'Interactive SaaS Placement Board Dashboard', 'tech': 'React, CSS Grid'})
    if len(certs) == 0:
        recommended_certs.append({'name': 'AWS Certified Cloud Practitioner', 'org': 'Amazon Web Services'})
        recommended_certs.append({'name': 'Google Advanced Data Analytics Certificate', 'org': 'Google'})
    else:
        recommended_certs.append({'name': 'HashiCorp Certified: Terraform Associate', 'org': 'HashiCorp'})
        
    if len(courses) < 2:
        courses.append({'title': 'System Design Interview Guide', 'platform': 'ByteByteGo'})
        courses.append({'title': 'SQL for Data Analytics and Analytics Engineering', 'platform': 'Coursera'})
    if len(recommended_projects) < 2:
        recommended_projects.append({'title': 'Task Manager REST API', 'tech': 'Node.js, SQLite, JWT'})
        recommended_projects.append({'title': 'Automated ATS File Parsing Scanner', 'tech': 'Flask, pdf-parser'})
        
    # 8. Weekly learning roadmap goals (beginner to advanced)
    weeks = [
        {
            'week': 1,
            'title': 'Core Language Foundation & Syntax',
            'goal': 'Master OOP principles, code structure conventions, and core loops.',
            'resources': 'Udemy Python/Java track, documentation guidelines.',
            'action_item': 'Implement sample CRUD logic inside a sandbox console.'
        },
        {
            'week': 2,
            'title': 'Relational Databases & SQL Schema Design',
            'goal': 'Design database blueprints, write index queries, and join tables.',
            'resources': 'SQLite documentation, schema builder tutorials.',
            'action_item': 'Build database schemas storing student activity logs.'
        },
        {
            'week': 3,
            'title': 'REST API Architecture & Frameworks Integration',
            'goal': 'Set up local dev servers, define REST request methods, verify tokens.',
            'resources': 'Flask / Express documentation guides.',
            'action_item': 'Coded Flask backend paths returning JSON payloads.'
        },
        {
            'week': 4,
            'title': 'Interview Simulation & Mock Practice',
            'goal': 'Simulate technical interview rounds covering data structures and mock logic.',
            'resources': 'LeetCode arrays, placement preparation manuals.',
            'action_item': 'Complete 5 conceptual exercises with time complexity bounds.'
        }
    ]
    
    return jsonify({
        'success': True,
        'cgpa': cgpa,
        'skills': skills,
        'ats_score': ats_score,
        'resume_strength': {
            'formatting': formatting_strength,
            'keyword_density': keyword_density,
            'section_completion': section_completion,
            'suggestions': suggestions
        },
        'matching_companies': matching_companies,
        'placement_prediction': {
            'score': final_prob,
            'breakdown': {
                'cgpa': round(cgpa_contrib, 1),
                'skills': round(skills_contrib, 1),
                'projects': round(projects_contrib, 1),
                'certs': round(certs_contrib, 1)
            }
        },
        'ai_recommendations': {
            'courses': courses,
            'certs': recommended_certs,
            'projects': recommended_projects
        },
        'roadmap': {
            'weeks': weeks
        }
    })

# -------------------------------------------------------------
# Production Module 1: Job Matching Module
# -------------------------------------------------------------
@app.route('/api/jobs', methods=['GET'])
@login_required
def get_jobs():
    db = get_db()
    cursor = db.cursor()
    
    # Fetch all jobs
    cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
    jobs_rows = cursor.fetchall()
    
    # Fetch student's latest resume extracted_text and skills
    user_id = session['user_id']
    cursor.execute('SELECT extracted_text FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
    resume = cursor.fetchone()
    resume_text = resume['extracted_text'].lower() if resume and resume['extracted_text'] else ""
    
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    profile_skills = [row['skill_name'].lower() for row in cursor.fetchall()]
    
    jobs_list = []
    for job in jobs_rows:
        reqs = [r.strip() for r in job['requirements'].split(',') if r.strip()]
        
        matched = []
        missing = []
        for req in reqs:
            req_l = req.lower()
            # Check matching in resume OR in profile skills
            if (resume_text and req_l in resume_text) or (req_l in profile_skills):
                matched.append(req)
            else:
                missing.append(req)
                
        # Calculate match percentage
        total_reqs = len(reqs)
        match_pct = 0
        if total_reqs > 0:
            match_pct = int((len(matched) / total_reqs) * 100)
            
        jobs_list.append({
            'id': job['id'],
            'title': job['title'],
            'company': job['company'],
            'description': job['description'],
            'requirements': job['requirements'],
            'match_percentage': match_pct,
            'matched_skills': matched,
            'missing_skills': missing
        })
        
    return jsonify({'success': True, 'jobs': jobs_list})

# -------------------------------------------------------------
# Production Module 2: Interview Preparation Module
# -------------------------------------------------------------
# Mock Interview banks
INTERVIEW_BANKS = {
    'technical_python': [
        {"question": "Explain the difference between deep copy and shallow copy in Python.", "answer": "Shallow copy duplicates references; Deep copy recursively copies objects."},
        {"question": "What is the Global Interpreter Lock (GIL) and how does it affect multi-threading?", "answer": "The GIL is a mutex preventing concurrent bytecode execution, limiting CPU-bound threads."},
        {"question": "How do generators work and what is the benefit of the 'yield' keyword?", "answer": "Generators yield values lazily, preserving memory overhead during iteration."},
        {"question": "What is a decorator and how do you write a custom one?", "answer": "A decorator modifies a function wrapper dynamically without altering its code structure."},
        {"question": "Explain Python's garbage collection and reference counting model.", "answer": "Python deletes objects when reference count hits zero, using a cyclic collector for circles."}
    ],
    'technical_sql': [
        {"question": "Explain the differences between INNER, LEFT, and RIGHT joins.", "answer": "INNER returns shared rows. LEFT returns all left rows plus matched right rows, etc."},
        {"question": "What is a database index and how does it speed up queries?", "answer": "An index is a pointer data structure allowing column checks without full table scans."},
        {"question": "What are window functions and how do they differ from GROUP BY?", "answer": "Window functions compute values without aggregating rows into single summaries."},
        {"question": "Describe database normalization and its key normal forms (1NF, 2NF, 3NF).", "answer": "Normalization prunes redundant relations, mapping fields across key constraints."},
        {"question": "What are transactions and what do ACID properties guarantee?", "answer": "ACID ensures Atomicity, Consistency, Isolation, and Durability on queries."}
    ],
    'technical_general': [
        {"question": "What is the difference between a process and a thread?", "answer": "Processes run isolated memory contexts; threads share parent process memory."},
        {"question": "Explain time complexity of lookup, insert, and delete in a Hash Map.", "answer": "Average case is O(1); worst case collapses to O(N) during collisions."},
        {"question": "How does HTTP work and what is the difference between GET and POST?", "answer": "HTTP is request-response. GET queries parameters in URL; POST packs payloads in body."},
        {"question": "What is a REST API and what are its core architectural principles?", "answer": "REST is a stateless, resource-oriented framework using HTTP methods."},
        {"question": "Describe how you resolve merge conflicts in Git workflows.", "answer": "Resolve by checking markers in conflicted files, testing logic, and committing."}
    ],
    'hr': [
        {"question": "Tell me about yourself and walk me through your background.", "answer": "Explain academic credentials, major projects, tool expertise, and core motivators."},
        {"question": "What are your greatest professional strengths and weaknesses?", "answer": "Cite solid competencies, and name a soft skill weakness you are active in resolving."},
        {"question": "Describe a conflict you faced in a group project and how you resolved it.", "answer": "Use STAR. Detail the challenge, key communication steps, and productive resolutions."},
        {"question": "Why do you want to work for our company?", "answer": "Align the company's research area or codebase with your growth objectives."},
        {"question": "Where do you see yourself in five years?", "answer": "State plans to master technical components and mentor junior programmers."}
    ]
}

@app.route('/api/interview/generate', methods=['POST'])
@login_required
def generate_interview():
    skill_name = request.form.get('skill_name', '').strip()
    question_type = request.form.get('question_type', '').strip()
    
    if not question_type:
        return jsonify({'success': False, 'message': 'Question type is required.'}), 400
        
    questions = []
    if question_type == 'HR':
        questions = INTERVIEW_BANKS['hr']
    else: # Technical
        skill_key = f"technical_{skill_name.lower()}"
        if skill_key in INTERVIEW_BANKS:
            questions = INTERVIEW_BANKS[skill_key]
        else:
            questions = INTERVIEW_BANKS['technical_general']
            
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO interviews (user_id, skill_name, question_type, questions_json) VALUES (?, ?, ?, ?)',
        (session['user_id'], skill_name or "General CS", question_type, json.dumps(questions))
    )
    db.commit()
    
    return jsonify({
        'success': True,
        'skill_name': skill_name or "General CS",
        'question_type': question_type,
        'questions': questions
    })

@app.route('/api/interview/history', methods=['GET'])
@login_required
def get_interview_history():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM interviews WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    rows = cursor.fetchall()
    
    history = []
    for r in rows:
        history.append({
            'id': r['id'],
            'skill_name': r['skill_name'],
            'question_type': r['question_type'],
            'questions': json.loads(r['questions_json']),
            'created_at': r['created_at']
        })
    return jsonify({'success': True, 'history': history})

# -------------------------------------------------------------
# Production Module 3: PDF Report Generation
# -------------------------------------------------------------
@app.route('/api/report/resume/<int:id>', methods=['GET'])
@login_required
def download_resume_report(id):
    db = get_db()
    cursor = db.cursor()
    
    # Verification
    if session.get('username') == 'admin':
        cursor.execute('SELECT r.*, u.username FROM resumes r JOIN users u ON r.user_id = u.id WHERE r.id = ?', (id,))
    else:
        cursor.execute('SELECT r.*, u.username FROM resumes r JOIN users u ON r.user_id = u.id WHERE r.id = ? AND r.user_id = ?', (id, session['user_id']))
    resume = cursor.fetchone()
    
    if not resume:
        return "Resume report not found.", 404
        
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f"ATS Resume Analysis Audit Report", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Candidate Username: {resume['username']}", ln=1)
    pdf.cell(0, 6, f"Filename: {resume['filename']}", ln=1)
    pdf.cell(0, 6, f"Date Evaluated: {resume['analyzed_at']}", ln=1)
    pdf.ln(8)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"1. ATS Matching Summary", ln=1)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, f"Calculated Grade Score: {resume['ats_score']}/100", ln=1)
    
    # Progress bar box
    pdf.set_fill_color(243, 244, 246)
    pdf.rect(10, pdf.get_y(), 190, 6, 'F')
    pdf.set_fill_color(37, 99, 235)
    pdf.rect(10, pdf.get_y(), int(190 * (resume['ats_score'] / 100)), 6, 'F')
    pdf.ln(10)
    
    # Detected and suggestions placeholder text (simulate analysis breakdown)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"2. Optimization Insights & Checklist", ln=1)
    pdf.set_font('Helvetica', '', 10)
    
    pdf.multi_cell(0, 6, "Below is a checklist of structural improvements based on the resume parsing run:\n"
                          "- Verify 'Education', 'Experience', and 'Projects' sections are clearly marked.\n"
                          "- Populate descriptions with key technical keywords like Python, SQL, React.\n"
                          "- Use action verbs at the start of bullet points in experience records.\n"
                          "- Ensure metrics (such as 'improved performance by 20%') are included.")
    
    response = make_response(pdf.output())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ATS_Audit_{resume["filename"]}'
    return response

@app.route('/api/report/prediction', methods=['GET'])
@login_required
def download_prediction_report():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    cursor.execute('SELECT username, cgpa FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or user['cgpa'] is None:
        return "Placement report error: profile set incomplete. Please update CGPA on dashboard.", 400
        
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    skills = [row['skill_name'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT title FROM projects WHERE user_id = ?', (user_id,))
    projects = [row['title'] for row in cursor.fetchall()]
    
    cursor.execute('SELECT cert_name FROM certifications WHERE user_id = ?', (user_id,))
    certs = [row['cert_name'] for row in cursor.fetchall()]
    
    # Calculate stats
    prob = 35.0
    cgpa_contrib = (user['cgpa'] / 10.0) * 30.0   # Indian CGPA scale: 0-10
    skills_contrib = min(15.0, len(skills) * 3.0)
    projects_contrib = min(12.0, len(projects) * 6.0)
    certs_contrib = min(8.0, len(certs) * 4.0)
    prob += cgpa_contrib + skills_contrib + projects_contrib + certs_contrib
    final_prob = min(99.0, round(prob, 1))
    
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f"AI Placement Predictive Analytics Report", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Candidate Username: {user['username']}", ln=1)
    pdf.cell(0, 6, f"Academic Benchmark CGPA: {user['cgpa']}", ln=1)
    pdf.ln(8)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"1. Calculated Placement Odds: {final_prob}%", ln=1)
    
    # Progress bar box
    pdf.set_fill_color(243, 244, 246)
    pdf.rect(10, pdf.get_y(), 190, 6, 'F')
    pdf.set_fill_color(16, 185, 129) # Emerald Green for placement
    pdf.rect(10, pdf.get_y(), int(190 * (final_prob / 100)), 6, 'F')
    pdf.ln(10)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"2. Profile Parameter Impact Breakdown", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"- Academic CGPA Contribution: {round(cgpa_contrib, 1)}% out of max 30%", ln=1)
    pdf.cell(0, 6, f"- Technical Skills Volume Contribution: {round(skills_contrib, 1)}% out of max 15%", ln=1)
    pdf.cell(0, 6, f"- Project Portfolios Contribution: {round(projects_contrib, 1)}% out of max 12%", ln=1)
    pdf.cell(0, 6, f"- Professional Certifications Contribution: {round(certs_contrib, 1)}% out of max 8%", ln=1)
    pdf.ln(8)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"3. Actionable Career Enhancement Guidelines", ln=1)
    pdf.set_font('Helvetica', '', 10)
    
    recs = []
    if user['cgpa'] < 3.0:
        recs.append("Prioritize academic indicators to clear recruitment filters.")
    if len(skills) < 4:
        recs.append("Register at least 4 tech keywords in your profile dashboard.")
    if len(projects) < 2:
        recs.append("Develop at least 2 portfolio repositories (e.g. backend Flask API).")
    if len(certs) < 1:
        recs.append("Acquire a professional certification (e.g. AWS practitioner).")
    if final_prob >= 85.0:
        recs.append("Outstanding profile match! Practice mock coding and HR interview prompts.")
        
    for r in recs:
        pdf.cell(0, 6, f"* {r}", ln=1)
        
    response = make_response(pdf.output())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Placement_Prediction_Report.pdf'
    return response

# -------------------------------------------------------------
# Production Module 4: Admin Dashboard Routes
# -------------------------------------------------------------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    # 1. Overview counts
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM resumes')
    total_resumes = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM contact_messages')
    total_messages = cursor.fetchone()['count']
    
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) as count FROM (
            SELECT user_id FROM skills 
            UNION 
            SELECT user_id FROM projects 
            UNION 
            SELECT user_id FROM resumes
        )
    ''')
    active_users = cursor.fetchone()['count']
    
    # 2. Recent Registrations (limit 5)
    cursor.execute('SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at DESC LIMIT 5')
    recent_registrations = cursor.fetchall()
    
    # 3. Resume Statistics
    cursor.execute('SELECT AVG(ats_score) as avg_score, MAX(ats_score) as max_score, MIN(ats_score) as min_score FROM resumes')
    res_stats = cursor.fetchone()
    resume_stats = {
        'avg': round(res_stats['avg_score'], 1) if res_stats['avg_score'] is not None else 0.0,
        'max': res_stats['max_score'] if res_stats['max_score'] is not None else 0,
        'min': res_stats['min_score'] if res_stats['min_score'] is not None else 0,
        'total': total_resumes
    }
    
    # 4. Detailed list of uploaded resumes
    cursor.execute('''
        SELECT r.id, r.filename, r.ats_score, r.analyzed_at, u.username, u.email 
        FROM resumes r 
        JOIN users u ON r.user_id = u.id 
        ORDER BY r.analyzed_at DESC
    ''')
    resumes_list = cursor.fetchall()
    
    # 5. Top Skills aggregated
    cursor.execute('''
        SELECT skill_name, COUNT(*) as count 
        FROM skills 
        GROUP BY LOWER(skill_name) 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    top_skills = cursor.fetchall()
    
    # 6. Fetch all users for roster and user management
    cursor.execute('SELECT id, username, email, cgpa, branch, gender, is_admin, created_at FROM users')
    users_rows = cursor.fetchall()
    
    students_list = []
    total_probability = 0
    calculated_cohort_count = 0
    
    for u in users_rows:
        u_id = u['id']
        cgpa = u['cgpa']
        
        cursor.execute('SELECT COUNT(*) as count FROM skills WHERE user_id = ?', (u_id,))
        sc = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM projects WHERE user_id = ?', (u_id,))
        pc = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM certifications WHERE user_id = ?', (u_id,))
        cc = cursor.fetchone()['count']
        
        cursor.execute('SELECT ats_score, id FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (u_id,))
        latest = cursor.fetchone()
        ats = latest['ats_score'] if latest else None
        res_id = latest['id'] if latest else None
        
        # Calculate placement likelihood
        prob = 0.0
        if cgpa is not None:
            prob = 35.0 + ((cgpa / 10.0) * 30.0) + min(15.0, sc * 3.0) + min(12.0, pc * 6.0) + min(8.0, cc * 4.0)
            prob = min(99.0, round(prob, 1))
            total_probability += prob
            calculated_cohort_count += 1
            
        # Build user activity list dynamically based on database contents
        activities = []
        if ats is not None:
            activities.append(f"Uploaded resume (ATS: {ats}%)")
        if sc > 0:
            activities.append(f"Logged {sc} technical skill parameters")
        if pc > 0:
            activities.append(f"Created {pc} codebase project profiles")
        if not activities:
            activities.append("User account registered (no resume/skills logged yet)")
            
        students_list.append({
            'id': u_id,
            'username': u['username'],
            'email': u['email'],
            'cgpa': cgpa,
            'branch': u['branch'] if u['branch'] else 'N/A',
            'gender': u['gender'] if u['gender'] else 'N/A',
            'is_admin': u['is_admin'],
            'created_at': u['created_at'],
            'skills_count': sc,
            'projects_count': pc,
            'certs_count': cc,
            'ats_score': ats,
            'resume_id': res_id,
            'placement_probability': prob if cgpa is not None else 'N/A',
            'activities': activities
        })
        
    avg_probability = 0.0
    if calculated_cohort_count > 0:
        avg_probability = round(total_probability / calculated_cohort_count, 1)
        
    # 7. Fetch all jobs
    cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
    jobs = cursor.fetchall()
    
    # 8. Fetch contact inquiries (including resolved status)
    cursor.execute('SELECT id, name, email, subject, message, created_at, resolved FROM contact_messages ORDER BY created_at DESC')
    inquiries = cursor.fetchall()
    
    return render_template(
        'admin.html',
        total_users=total_users,
        total_resumes=total_resumes,
        total_messages=total_messages,
        active_users=active_users,
        recent_registrations=recent_registrations,
        resume_stats=resume_stats,
        resumes_list=resumes_list,
        avg_probability=avg_probability,
        top_skills=top_skills,
        students=students_list,
        jobs=jobs,
        inquiries=inquiries
    )

# Admin Add Job Endpoint
@app.route('/admin/api/add-job', methods=['POST'])
@admin_required
def admin_add_job():
    title = request.form.get('title', '').strip()
    company = request.form.get('company', '').strip()
    description = request.form.get('description', '').strip()
    requirements = request.form.get('requirements', '').strip()
    
    if not title or not company or not requirements:
        return jsonify({'success': False, 'message': 'Job title, company, and skills requirements are required.'}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO jobs (title, company, description, requirements) VALUES (?, ?, ?, ?)',
        (title, company, description, requirements)
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Job opening registered successfully.'})

# Admin Charts JSON Endpoint (for rendering analytics widgets dynamically)
@app.route('/admin/api/charts-data', methods=['GET'])
@admin_required
def admin_charts_data():
    db = get_db()
    cursor = db.cursor()
    
    # 1. Skill Distribution (Count of students possessing each skill)
    cursor.execute('''
        SELECT skill_name, COUNT(*) as count 
        FROM skills 
        GROUP BY LOWER(skill_name) 
        ORDER BY count DESC 
        LIMIT 8
    ''')
    skills_rows = cursor.fetchall()
    skills_labels = [row['skill_name'] for row in skills_rows]
    skills_counts = [row['count'] for row in skills_rows]
    
    # 2. ATS Score Trends
    # Segregate resumes by ranges: <50, 50-70, 70-85, 85+
    cursor.execute('SELECT ats_score FROM resumes')
    scores = [row['ats_score'] for row in cursor.fetchall()]
    
    ats_ranges = {
        'Needs Improvement (<50)': 0,
        'Intermediate (50-70)': 0,
        'Competitive (70-85)': 0,
        'Top Candidate (85+)': 0
    }
    for s in scores:
        if s < 50:
            ats_ranges['Needs Improvement (<50)'] += 1
        elif s < 70:
            ats_ranges['Intermediate (50-70)'] += 1
        elif s < 85:
            ats_ranges['Competitive (70-85)'] += 1
        else:
            ats_ranges['Top Candidate (85+)'] += 1
            
    # 3. Placement Prediction Cohort Distribution
    # Group probabilities: <50%, 50-70%, 70-85%, 85%+
    cursor.execute('SELECT id, cgpa FROM users WHERE is_admin = 0')
    students = cursor.fetchall()
    
    placement_ranges = {
        'Risk Cohort (<50%)': 0,
        'Average Odds (50-70%)': 0,
        'High Potential (70-85%)': 0,
        'Guaranteed Match (85%+)': 0
    }
    
    for s in students:
        s_id = s['id']
        cgpa = s['cgpa']
        if cgpa is not None:
            # Recompute probability
            cursor.execute('SELECT COUNT(*) as count FROM skills WHERE user_id = ?', (s_id,))
            sc = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM projects WHERE user_id = ?', (s_id,))
            pc = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM certifications WHERE user_id = ?', (s_id,))
            cc = cursor.fetchone()['count']
            
            prob = 35.0 + ((cgpa / 10.0) * 30.0) + min(15.0, sc * 3.0) + min(12.0, pc * 6.0) + min(8.0, cc * 4.0)
            prob = min(99.0, prob)
            
            if prob < 50:
                placement_ranges['Risk Cohort (<50%)'] += 1
            elif prob < 70:
                placement_ranges['Average Odds (50-70%)'] += 1
            elif prob < 85:
                placement_ranges['High Potential (70-85%)'] += 1
            else:
                placement_ranges['Guaranteed Match (85%+)'] += 1
                
    # 4. Most selected companies (Target check)
    cursor.execute('''
        SELECT company_name, COUNT(*) as count 
        FROM user_dream_company 
        GROUP BY LOWER(company_name) 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    companies_rows = cursor.fetchall()
    companies_labels = [row['company_name'] for row in companies_rows]
    companies_counts = [row['count'] for row in companies_rows]
    
    # 5. User growth over time (cumulative count of all users)
    cursor.execute('''
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
        FROM users 
        GROUP BY month 
        ORDER BY month ASC
    ''')
    growth_rows = cursor.fetchall()
    growth_labels = []
    growth_counts = []
    cumulative = 0
    for row in growth_rows:
        m = row['month'] if row['month'] else '2026-07'
        cumulative += row['count']
        growth_labels.append(m)
        growth_counts.append(cumulative)
        
    return jsonify({
        'success': True,
        'skills': {
            'labels': skills_labels,
            'data': skills_counts
        },
        'ats': {
            'labels': list(ats_ranges.keys()),
            'data': list(ats_ranges.values())
        },
        'placement': {
            'labels': list(placement_ranges.keys()),
            'data': list(placement_ranges.values())
        },
        'companies': {
            'labels': companies_labels,
            'data': companies_counts
        },
        'growth': {
            'labels': growth_labels,
            'data': growth_counts
        }
    })

# -------------------------------------------------------------
# -------------------------------------------------------------
# Production Module 5: Dream Company Roadmap / Analyzer
# -------------------------------------------------------------
@app.route('/api/roadmap/companies-by-filter', methods=['POST'])
@login_required
def get_companies_by_filter():
    branch = request.form.get('branch', '').strip()
    city = request.form.get('city', '').strip()
    type_filter = request.form.get('type', '').strip()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM companies WHERE city = ? ORDER BY name ASC', (city,))
    all_companies = cursor.fetchall()
    
    # Query user details to calculate match scores
    user_id = session['user_id']
    cursor.execute('SELECT cgpa, branch FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    user_cgpa = user['cgpa'] if user['cgpa'] is not None else 0.0
    
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    user_skills = set(row['skill_name'].lower().strip() for row in cursor.fetchall())
    
    filtered_companies = []
    for c in all_companies:
        company_branches = [b.strip().upper() for b in c['branches'].split(',')]
        
        # Determine if company accepts this branch based on heuristics
        matched = False
        branch_upper = branch.upper().strip() if branch else ''
        
        is_service_based = (c['type'].lower() == 'service based' or 'service' in c['type'].lower())
        is_core_eng_company = (c['type'].lower() == 'core engineering' or 'core' in c['type'].lower())
        
        if not branch or branch_upper in ['ALL', 'ALL BRANCHES', 'ALL BRANCH', 'OTHERS', 'OTHER ENGINEERING BRANCHES', '']:
            matched = True
        elif is_service_based:
            # Service-based companies accept all branches
            matched = True
        elif branch_upper in ['ME', 'MECHANICAL', 'CE', 'CIVIL', 'CHEMICAL', 'BIOTECHNOLOGY', 'AEROSPACE', 'INSTRUMENTATION', 'EEE', 'ROBOTICS'] and is_core_eng_company:
            # Core engineering companies accept core engineering branches
            matched = True
        elif branch_upper in ['AI', 'AIML', 'AI/ML', 'AIDS', 'AI&DS', 'AI & DS', 'DATA SCIENCE']:
            # AI and Data Science branches match AI/ML, DS, or General CS/IT requirements
            matched = any(b in company_branches for b in ['AI', 'AIML', 'AIDS', 'AI & DS', 'AI/ML', 'AI&DS', 'CSE', 'IT'])
        elif branch_upper in ['IT', 'ISE', 'CSE']:
            # Software branches match each other for software positions
            matched = any(b in company_branches for b in ['CSE', 'IT', 'ISE'])
        elif branch_upper in ['CYBER SECURITY', 'CYBERSECURITY', 'CYBER']:
            matched = any(b in company_branches for b in ['CSE', 'IT', 'CYBER'])
        elif branch_upper in ['ECE', 'EEE', 'INSTRUMENTATION', 'ROBOTICS']:
            matched = any(b in company_branches for b in ['ECE', 'EEE', 'CSE', 'IT'])
        else:
            matched = (branch_upper in company_branches)
            
        if matched:
            # Type filter match (e.g. Product Based, Startups, Service Based, etc.)
            if type_filter and type_filter not in ['All Companies', 'All Types', 'All (245+)']:
                norm_filter = type_filter.lower().replace(' companies', '').replace(' based', '').strip()
                norm_type = c['type'].lower().replace(' companies', '').replace(' based', '').strip()
                if norm_filter not in norm_type:
                    continue
            
            # Simple match score calculation
            req_tech = [s.strip().lower() for s in c['tech_skills'].split(',') if s.strip()]
            matched_count = sum(1 for s in req_tech if s in user_skills)
            
            skill_score = (matched_count / len(req_tech)) * 100 if req_tech else 100
            cgpa_score = 100 if user_cgpa >= c['min_cgpa'] else (user_cgpa / c['min_cgpa']) * 100 if c['min_cgpa'] > 0 else 100
            
            match_score = int(skill_score * 0.7 + cgpa_score * 0.3)
            match_score = min(100, max(10, match_score))
            
            filtered_companies.append({
                'name': c['name'],
                'city': c['city'],
                'type': c['type'],
                'branches': c['branches'],
                'hiring_roles': c['hiring_roles'],
                'package_range': c['package_range'],
                'match_score': match_score,
                'min_cgpa': c['min_cgpa'],
                'logo_url': c['logo_url'],
                'hq': c['hq'],
                'bangalore_office': c['bangalore_office'],
                'website': c['website'],
                'careers_page': c['careers_page'],
                'employee_count': c['employee_count'],
                'industry': c['industry'],
                'founded_year': c['founded_year'],
                'description': c['description'],
                'hiring_process': c['hiring_process']
            })
            
    # Sort companies by match score descending
    filtered_companies.sort(key=lambda x: x['match_score'], reverse=True)
            
    return jsonify({'success': True, 'companies': filtered_companies})

@app.route('/api/roadmap/companies/<city>', methods=['GET'])
@login_required
def get_roadmap_companies(city):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT name FROM companies WHERE city = ? ORDER BY name ASC', (city,))
    companies = [row['name'] for row in cursor.fetchall()]
    return jsonify({'success': True, 'companies': companies})

@app.route('/api/roadmap/company-skills/<company>', methods=['GET'])
@login_required
def get_company_skills(company):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT skill_name FROM company_skills WHERE company_name = ?', (company,))
    skills = [row['skill_name'] for row in cursor.fetchall()]
    return jsonify({'success': True, 'skills': skills})

@app.route('/api/roadmap/set-dream-company', methods=['POST'])
@login_required
def set_dream_company():
    company = request.form.get('company', '').strip()
    city = request.form.get('city', '').strip()
    if not company or not city:
        return jsonify({'success': False, 'message': 'Company name and city are required.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    cursor.execute('SELECT id FROM user_dream_company WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('UPDATE user_dream_company SET company_name = ?, city = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (company, city, user_id))
    else:
        cursor.execute('INSERT INTO user_dream_company (user_id, company_name, city) VALUES (?, ?, ?)', (user_id, company, city))
    db.commit()
    return jsonify({'success': True, 'message': f'Dream company set to {company} ({city})'})

@app.route('/api/roadmap/clear', methods=['POST'])
@login_required
def clear_dream_company():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM user_dream_company WHERE user_id = ?', (session['user_id'],))
    db.commit()
    return jsonify({'success': True, 'message': 'Dream company cleared successfully.'})

@app.route('/api/roadmap/analysis', methods=['GET'])
@login_required
def get_roadmap_analysis():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    cursor.execute('SELECT company_name, city FROM user_dream_company WHERE user_id = ?', (user_id,))
    dream = cursor.fetchone()
    if not dream:
        return jsonify({'success': False, 'message': 'No dream company selected.'}), 404
        
    company_name = dream['company_name']
    city = dream['city']
    
    cursor.execute('SELECT * FROM companies WHERE name = ? AND city = ?', (company_name, city))
    company_info = cursor.fetchone()
    if not company_info:
        cursor.execute('SELECT * FROM companies WHERE name = ? LIMIT 1', (company_name,))
        company_info = cursor.fetchone()
        
    if not company_info:
        return jsonify({'success': False, 'message': 'Company details not found.'}), 404
        
    cursor.execute('SELECT cgpa, branch FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    user_cgpa = user['cgpa'] if user['cgpa'] is not None else 0.0
    user_branch = user['branch'] if user['branch'] is not None else "CSE"
    
    cursor.execute('SELECT skill_name FROM skills WHERE user_id = ?', (user_id,))
    user_skills = [row['skill_name'].lower().strip() for row in cursor.fetchall()]
    user_skills_set = set(user_skills)
    
    cursor.execute('SELECT cert_name FROM certifications WHERE user_id = ?', (user_id,))
    user_certs = [row['cert_name'].lower().strip() for row in cursor.fetchall()]
    
    cursor.execute('SELECT title, technologies FROM projects WHERE user_id = ?', (user_id,))
    user_projects = []
    for r in cursor.fetchall():
        user_projects.append(r['title'].lower().strip())
        if r['technologies']:
            for t in r['technologies'].split(','):
                user_projects.append(t.lower().strip())
                
    cursor.execute('SELECT ats_score FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
    resume = cursor.fetchone()
    ats_score = resume['ats_score'] if resume else 70.0
    
    req_tech = [s.strip() for s in company_info['tech_skills'].split(',') if s.strip()]
    req_soft = [s.strip() for s in company_info['soft_skills'].split(',') if s.strip()]
    pref_certs = [c.strip() for c in company_info['pref_certs'].split(',') if c.strip()]
    pref_projects = [p.strip() for p in company_info['pref_projects'].split(',') if p.strip()]
    min_cgpa = company_info['min_cgpa']
    
    matched_tech = []
    missing_tech = []
    for s in req_tech:
        if s.lower().strip() in user_skills_set:
            matched_tech.append(s)
        else:
            missing_tech.append(s)
            
    matched_soft = []
    missing_soft = []
    for s in req_soft:
        if s.lower().strip() in user_skills_set:
            matched_soft.append(s)
        else:
            missing_soft.append(s)
            
    matched_certs = []
    missing_certs = []
    for c in pref_certs:
        matched = False
        for uc in user_certs:
            if c.lower().strip() in uc or uc in c.lower().strip():
                matched = True
                break
        if matched:
            matched_certs.append(c)
        else:
            missing_certs.append(c)
            
    matched_projects = []
    missing_projects = []
    for p in pref_projects:
        matched = False
        for up in user_projects:
            if p.lower().strip() in up or up in p.lower().strip():
                matched = True
                break
        if matched:
            matched_projects.append(p)
        else:
            missing_projects.append(p)
            
    total_req_skills = len(req_tech) + len(req_soft)
    matched_skills_count = len(matched_tech) + len(matched_soft)
    skill_match_pct = 0
    if total_req_skills > 0:
        skill_match_pct = int((matched_skills_count / total_req_skills) * 100)
    else:
        skill_match_pct = 100
        
    tech_w = (len(matched_tech) / len(req_tech) * 40.0) if req_tech else 40.0
    soft_w = (len(matched_soft) / len(req_soft) * 10.0) if req_soft else 10.0
    cgpa_w = 25.0 if user_cgpa >= min_cgpa else ((user_cgpa / min_cgpa) * 25.0 if min_cgpa > 0 else 25.0)
    certs_w = (len(matched_certs) / len(pref_certs) * 15.0) if pref_certs else 15.0
    projects_w = (len(matched_projects) / len(pref_projects) * 10.0) if pref_projects else 10.0
    
    readiness_score = int(tech_w + soft_w + cgpa_w + certs_w + projects_w)
    readiness_score = min(100, max(0, readiness_score))
    
    cgpa_contrib = (user_cgpa / 10.0) * 100.0
    placement_prob = int(0.5 * readiness_score + 0.3 * cgpa_contrib + 0.2 * ats_score)
    placement_prob = min(99, max(10, placement_prob))
    
    profile_cgpa = (user_cgpa / 10.0) * 30.0
    profile_skills = min(30.0, len(user_skills) * 4.0)
    profile_projects = min(20.0, len(user_projects) * 5.0)
    profile_certs = min(20.0, len(user_certs) * 10.0)
    profile_strength = int(profile_cgpa + profile_skills + profile_projects + profile_certs)
    profile_strength = min(100, max(10, profile_strength))
    
    missing_all_skills = missing_tech + missing_soft
    roadmap = []
    weeks_labels = ["Week 1-2", "Week 3-4", "Week 5-6", "Week 7-8", "Week 9-10"]
    
    if len(missing_all_skills) == 0:
        roadmap.append({
            'week': 'Week 1-10',
            'skill': 'Advanced Optimization & Mock Interviews',
            'youtube_url': 'https://www.youtube.com/results?search_query=Technical+Interview+Preparation',
            'cert_url': 'https://www.hackerrank.com/certificates',
            'practice_url': 'https://leetcode.com/'
        })
    else:
        for idx, skill in enumerate(missing_all_skills):
            week_idx = min(4, idx)
            cursor.execute('SELECT youtube_url, cert_url, practice_url FROM learning_resources WHERE LOWER(skill_name) = ?', (skill.lower().strip(),))
            res = cursor.fetchone()
            if res:
                youtube = res['youtube_url']
                cert = res['cert_url']
                practice = res['practice_url']
            else:
                youtube = f"https://www.youtube.com/results?search_query=Learn+{skill}+Basics"
                cert = "https://www.freecodecamp.org/"
                practice = "https://leetcode.com/"
                
            roadmap.append({
                'week': weeks_labels[week_idx],
                'skill': skill,
                'youtube_url': youtube,
                'cert_url': cert,
                'practice_url': practice
            })
            
    return jsonify({
        'success': True,
        'company_name': company_name,
        'city': city,
        'type': company_info['type'],
        'hiring_roles': company_info['hiring_roles'],
        'package_range': company_info['package_range'],
        'expected_cgpa': min_cgpa,
        'logo_url': company_info['logo_url'],
        'hq': company_info['hq'],
        'bangalore_office': company_info['bangalore_office'],
        'website': company_info['website'],
        'careers_page': company_info['careers_page'],
        'employee_count': company_info['employee_count'],
        'industry': company_info['industry'],
        'founded_year': company_info['founded_year'],
        'description': company_info['description'],
        'hiring_process': company_info['hiring_process'],
        'tech_skills': company_info['tech_skills'],
        'soft_skills': company_info['soft_skills'],
        'pref_certs': company_info['pref_certs'],
        'pref_projects': company_info['pref_projects'],
        'readiness_score': readiness_score,
        'placement_probability': placement_prob,
        'skill_match_pct': skill_match_pct,
        'profile_strength': profile_strength,
        'matched_tech': matched_tech,
        'missing_tech': missing_tech,
        'matched_soft': matched_soft,
        'missing_soft': missing_soft,
        'matched_certs': matched_certs,
        'missing_certs': missing_certs,
        'matched_projects': matched_projects,
        'missing_projects': missing_projects,
        'roadmap': roadmap
    })

# Portfolio Contact API route - open for public recruiter outreach
@app.route('/api/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    
    if not name or not email or not subject or not message:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
        
    if '@' not in email or '.' not in email:
        return jsonify({'success': False, 'message': 'Please provide a valid email address.'}), 400
        
    user_id = session.get('user_id') if 'user_id' in session else None
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO contact_messages (user_id, name, email, subject, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, name, email, subject, message))
    db.commit()
    
    # Mock simulated email dispatch in terminal logs
    print("\n" + "="*50)
    print("MOCK SMTP EMAIL SENT:")
    print(f"From: {email} ({name})")
    print(f"To: portfolio-owner@placement-assistant.com")
    print(f"Subject: [Portfolio Contact] {subject}")
    print(f"Message Content:\n{message}")
    print("="*50 + "\n")
    
    return jsonify({'success': True, 'message': 'Thank you! Your message has been sent successfully.'})

# Public Pages Routes
@app.route('/about')
def about():
    user = None
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username, email, branch, cgpa FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('about.html', user=user)

@app.route('/features')
def features_page():
    user = None
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username, email, branch, cgpa FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('features.html', user=user)

@app.route('/contact')
def contact_page():
    user = None
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username, email, branch, cgpa FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('contact.html', user=user)

# Public Portfolio Resume dynamic PDF download route
@app.route('/contact/resume/download', methods=['GET'])
def download_portfolio_resume():
    pdf = ResumePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Header Banner - Accent Blue
    pdf.set_fill_color(37, 99, 235) # #2563EB
    pdf.rect(10, 10, 190, 8, 'F')
    pdf.ln(12)
    
    # Title / Name
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.set_font('Helvetica', 'B', 22)
    pdf.cell(0, 10, "Chinmayi S R", ln=1, align='L')
    
    # Subtitle / Education Area
    pdf.set_text_color(37, 99, 235) # Blue Accent
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 6, "BE CSE Student | Web Developer | AI Enthusiast", ln=1, align='L')
    
    # Contacts
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.set_font('Helvetica', '', 9.5)
    pdf.cell(0, 6, "Email: chinnu3026@gmail.com | Location: Bengaluru, Karnataka, India", ln=1, align='L')
    pdf.cell(0, 6, "LinkedIn: linkedin.com/in/chinnu3026 | GitHub: github.com/chinnu3026", ln=1, align='L')
    pdf.ln(4)
    
    # Horizontal line separator
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # ACADEMIC PROFILE
    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "ACADEMIC PROFILE", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, "Degree: Bachelor of Engineering in Computer Science & Engineering", ln=1)
    pdf.cell(0, 6, "Institution: Visvesvaraya Technological University (VTU) Affiliate | CGPA: 9.10/10.00", ln=1)
    pdf.ln(4)
    
    # TECHNICAL SKILLS
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "TECHNICAL SKILLS", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, "Languages: Python, JavaScript, HTML5, CSS3, SQL\n"
                          "Frameworks & Libraries: Flask, React, Bootstrap 5, Express.js\n"
                          "Tools & Databases: Git, SQLite, PostgreSQL, REST APIs, AI Prompting")
    pdf.ln(4)
        
    # PROJECTS
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "ACADEMIC & PERSONAL PROJECTS", ln=1)
    
    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.cell(0, 6, "AI Career & Placement Assistant Platform | Stack: Flask, SQLite, Bootstrap 5, Chart.js", ln=1)
    pdf.set_font('Helvetica', '', 9.5)
    pdf.multi_cell(0, 5, "Developed a modern placement intelligence panel storing candidate profiles, tracking interview evaluations, and calculating job readiness indicators. Built a real-time resume audit check, skill gap recommendation engine, and dynamic company tracking.")
    pdf.ln(2.5)

    pdf.set_font('Helvetica', 'B', 10.5)
    pdf.cell(0, 6, "Chat & Collaboration Dashboard | Stack: React, CSS variables, Node.js", ln=1)
    pdf.set_font('Helvetica', '', 9.5)
    pdf.multi_cell(0, 5, "Designed a real-time responsive chat and work monitoring app using modern glassmorphism design parameters, responsive layouts, and micro-animations.")
    pdf.ln(4)
        
    # CERTIFICATIONS
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "CERTIFICATIONS", ln=1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, "- AWS Certified Cloud Practitioner (Amazon Web Services)", ln=1)
    pdf.cell(0, 6, "- Google Advanced AI Professional Certificate (Google)", ln=1)
        
    response = make_response(pdf.output())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=Resume_Chinmayi_SR.pdf'
    return response

# Resume dynamic PDF generator helper class
class ResumePDF(FPDF):
    def header(self):
        pass
    def footer(self):
        self.set_y(-15)
        self.set_text_color(156, 163, 175)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, 'Generated via AI Career & Placement Assistant Portfolio', align='C')

# Dynamic portfolio resume download route
@app.route('/api/contact/resume/download', methods=['GET'])
@login_required
def download_resume():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    # 1. Try to fetch the latest uploaded resume PDF from the ATS resumes database
    cursor.execute('SELECT filename FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (user_id,))
    row = cursor.fetchone()
    if row and row['filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
        if os.path.exists(file_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], row['filename'], as_attachment=True)
            
    # 2. Fallback: dynamically generate a beautiful resume report from database data
    cursor.execute('SELECT username, email, branch, cgpa FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    cursor.execute('SELECT skill_name, proficiency FROM skills WHERE user_id = ?', (user_id,))
    skills = cursor.fetchall()
    
    cursor.execute('SELECT cert_name, issuing_org, issue_date FROM certifications WHERE user_id = ?', (user_id,))
    certs = cursor.fetchall()
    
    cursor.execute('SELECT title, description, technologies FROM projects WHERE user_id = ?', (user_id,))
    projects = cursor.fetchall()
    
    pdf = ResumePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Header Banner - Accent Blue
    pdf.set_fill_color(37, 99, 235) # #2563EB
    pdf.rect(10, 10, 190, 8, 'F')
    pdf.ln(12)
    
    # Title / Name
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.set_font('Helvetica', 'B', 22)
    name = user['username'].replace('_', ' ').title() if user else 'John Developer'
    pdf.cell(0, 10, name, ln=1, align='L')
    
    # Subtitle / Education Area
    pdf.set_text_color(37, 99, 235) # Blue Accent
    pdf.set_font('Helvetica', 'B', 11)
    branch_name = user['branch'] if (user and user['branch']) else 'Computer Science Engineering'
    pdf.cell(0, 6, f"Candidate for B.E. in {branch_name}", ln=1, align='L')
    
    # Contacts
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.set_font('Helvetica', '', 9.5)
    email_addr = user['email'] if user else 'chinnu3026@gmail.com'
    pdf.cell(0, 6, f"Email: {email_addr} | Location: Bengaluru, Karnataka, India", ln=1, align='L')
    pdf.cell(0, 6, "LinkedIn: linkedin.com/in/chinnu3026 | GitHub: github.com/chinnu3026", ln=1, align='L')
    pdf.ln(4)
    
    # Horizontal line separator
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # ACADEMIC PROFILE
    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "ACADEMIC PROFILE", ln=1)
    pdf.set_font('Helvetica', '', 10)
    cgpa_val = f"{user['cgpa']:.2f}" if (user and user['cgpa'] is not None) else "8.50"
    pdf.cell(0, 6, f"Institution: Visvesvaraya Technological University Affiliate | CGPA: {cgpa_val}/10.00", ln=1)
    pdf.cell(0, 6, f"Degree: Bachelor of Engineering in {branch_name}", ln=1)
    pdf.ln(4)
    
    # TECHNICAL SKILLS
    if skills:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, "TECHNICAL SKILLS", ln=1)
        pdf.set_font('Helvetica', '', 10)
        skills_str = ", ".join([f"{s['skill_name']} ({s['proficiency']})" for s in skills])
        pdf.multi_cell(0, 6, skills_str)
        pdf.ln(4)
    else:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, "TECHNICAL SKILLS", ln=1)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, "Python (Advanced), SQL (Intermediate), Git (Intermediate)", ln=1)
        pdf.ln(4)
        
    # PROJECTS
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "ACADEMIC & PERSONAL PROJECTS", ln=1)
    if projects:
        for proj in projects:
            pdf.set_font('Helvetica', 'B', 10.5)
            pdf.cell(0, 6, f"{proj['title']} | Stack: {proj['technologies']}", ln=1)
            pdf.set_font('Helvetica', '', 9.5)
            pdf.multi_cell(0, 5, proj['description'])
            pdf.ln(2.5)
    else:
        pdf.set_font('Helvetica', 'B', 10.5)
        pdf.cell(0, 6, "AI Career Assistant Portal | Stack: Flask, SQLite, Bootstrap 5", ln=1)
        pdf.set_font('Helvetica', '', 9.5)
        pdf.multi_cell(0, 5, "Developed a modern placement intelligence panel storing candidate profiles, tracking interview evaluations, and calculating job readiness indicators.")
        pdf.ln(2.5)
    pdf.ln(2)
        
    # CERTIFICATIONS
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, "CERTIFICATIONS", ln=1)
    pdf.set_font('Helvetica', '', 10)
    if certs:
        for cert in certs:
            pdf.cell(0, 6, f"- {cert['cert_name']} (Issued by {cert['issuing_org']}, {cert['issue_date']})", ln=1)
    else:
        pdf.cell(0, 6, "- AWS Certified Cloud Practitioner (Amazon Web Services)", ln=1)
        
    response = make_response(pdf.output())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Resume_{user["username"] if user else "Candidate"}.pdf'
    return response

# CSV / Excel export APIs
import csv
from io import StringIO

@app.route('/admin/api/export/students', methods=['GET'])
@login_required
def export_students_csv():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return "Unauthorized", 403
        
    cursor.execute('SELECT id, username, email, cgpa, branch, gender, is_admin FROM users')
    users = cursor.fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Username', 'Email', 'CGPA', 'Branch', 'Gender', 'Role', 'Skills Count', 'Projects Count', 'Certifications Count', 'Latest ATS Score', 'Estimated Placement Odds'])
    
    for u in users:
        u_id = u['id']
        cursor.execute('SELECT COUNT(*) as count FROM skills WHERE user_id = ?', (u_id,))
        sc = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM projects WHERE user_id = ?', (u_id,))
        pc = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM certifications WHERE user_id = ?', (u_id,))
        cc = cursor.fetchone()['count']
        cursor.execute('SELECT ats_score FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (u_id,))
        latest = cursor.fetchone()
        ats = latest['ats_score'] if latest else 'N/A'
        
        prob = 'N/A'
        if u['cgpa'] is not None:
            prob_calc = 35.0 + ((u['cgpa'] / 10.0) * 30.0) + min(15.0, sc * 3.0) + min(12.0, pc * 6.0) + min(8.0, cc * 4.0)
            prob = f"{min(99.0, round(prob_calc, 1))}%"
            
        role = 'Admin' if u['is_admin'] else 'Student'
        cw.writerow([
            u['id'],
            u['username'],
            u['email'],
            u['cgpa'] if u['cgpa'] is not None else 'N/A',
            u['branch'] if u['branch'] else 'N/A',
            u['gender'] if u['gender'] else 'N/A',
            role,
            sc,
            pc,
            cc,
            ats,
            prob
        ])
        
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=student_cohort_roster.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/admin/api/export/inquiries', methods=['GET'])
@login_required
def export_inquiries_csv():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return "Unauthorized", 403
        
    cursor.execute('SELECT * FROM contact_messages ORDER BY created_at DESC')
    inquiries = cursor.fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Message ID', 'Sender Name', 'Sender Email', 'Subject', 'Message Content', 'Created At'])
    
    for inq in inquiries:
        cw.writerow([
            inq['id'],
            inq['name'],
            inq['email'],
            inq['subject'],
            inq['message'],
            inq['created_at']
        ])
        
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=contact_inquiries.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

# User Management APIs (Toggle Role, Delete User)
@app.route('/admin/api/user/toggle-role', methods=['POST'])
@login_required
def toggle_user_role():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403
        
    target_user_id = request.form.get('user_id')
    if not target_user_id:
        return jsonify({'success': False, 'message': 'Missing user ID.'}), 400
        
    if int(target_user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'You cannot change your own role.'}), 400
        
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (target_user_id,))
    target_user = cursor.fetchone()
    if not target_user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404
        
    new_role = 0 if target_user['is_admin'] else 1
    cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_role, target_user_id))
    db.commit()
    
    role_name = 'Admin' if new_role else 'Student'
    return jsonify({'success': True, 'message': f'User role updated to {role_name} successfully.'})

@app.route('/admin/api/user/delete', methods=['POST'])
@login_required
def delete_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403
        
    target_user_id = request.form.get('user_id')
    if not target_user_id:
        return jsonify({'success': False, 'message': 'Missing user ID.'}), 400
        
    if int(target_user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'You cannot delete your own account.'}), 400
        
    cursor.execute('DELETE FROM users WHERE id = ?', (target_user_id,))
    cursor.execute('DELETE FROM skills WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM certifications WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM projects WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM resumes WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM user_dream_company WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM saved_companies WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM application_tracker WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM placement_calendar WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM coding_progress WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM recruiter_evaluations WHERE user_id = ?', (target_user_id,))
    cursor.execute('DELETE FROM readiness_scores WHERE user_id = ?', (target_user_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'User account deleted successfully.'})

# Contact Inquiry Management API (Delete Inquiry)
@app.route('/admin/api/inquiry/delete', methods=['POST'])
@login_required
def delete_inquiry():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403
        
    inquiry_id = request.form.get('inquiry_id')
    if not inquiry_id:
        return jsonify({'success': False, 'message': 'Missing inquiry ID.'}), 400
        
    cursor.execute('DELETE FROM contact_messages WHERE id = ?', (inquiry_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Inquiry message deleted successfully.'})

# Admin Resolve Inquiry Endpoint
@app.route('/admin/api/inquiry/resolve', methods=['POST'])
@login_required
def resolve_inquiry():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403
        
    inquiry_id = request.form.get('inquiry_id')
    if not inquiry_id:
        return jsonify({'success': False, 'message': 'Missing inquiry ID.'}), 400
        
    cursor.execute('SELECT resolved FROM contact_messages WHERE id = ?', (inquiry_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'success': False, 'message': 'Inquiry not found.'}), 404
        
    new_status = 0 if row['resolved'] else 1
    cursor.execute('UPDATE contact_messages SET resolved = ? WHERE id = ?', (new_status, inquiry_id))
    db.commit()
    
    status_text = 'Resolved' if new_status else 'Unresolved'
    return jsonify({'success': True, 'message': f'Inquiry marked as {status_text} successfully.', 'resolved': new_status})

# Admin Edit User Details Endpoint
@app.route('/admin/api/user/edit', methods=['POST'])
@login_required
def admin_edit_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized access.'}), 403
        
    target_user_id = request.form.get('user_id')
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    cgpa_raw = request.form.get('cgpa', '').strip()
    branch = request.form.get('branch', '').strip()
    
    if not target_user_id or not username or not email:
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400
        
    try:
        cgpa = float(cgpa_raw) if cgpa_raw else None
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid CGPA value.'}), 400
        
    cursor.execute('UPDATE users SET username = ?, email = ?, cgpa = ?, branch = ? WHERE id = ?', 
                   (username, email, cgpa, branch, target_user_id))
    db.commit()
    return jsonify({'success': True, 'message': 'User details updated successfully.'})

# Admin Download Resume Endpoint
@app.route('/admin/api/resume/download/<int:resume_id>', methods=['GET'])
@login_required
def admin_download_resume(resume_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return "Unauthorized", 403
        
    cursor.execute('SELECT filename FROM resumes WHERE id = ?', (resume_id,))
    row = cursor.fetchone()
    if row and row['filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
        if os.path.exists(file_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], row['filename'], as_attachment=True)
    return "Resume file not found.", 404

# Export students to Excel (compatibility mode XLS)
@app.route('/admin/api/export/students/excel', methods=['GET'])
@login_required
def export_students_excel():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    if not admin_user or not admin_user['is_admin']:
        return "Unauthorized", 403
        
    cursor.execute('SELECT id, username, email, cgpa, branch, gender, is_admin FROM users')
    users = cursor.fetchall()
    
    html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
    html += '<head><meta http-equiv="Content-type" content="text/html;charset=utf-8" /></head><body>'
    html += '<table border="1">'
    html += '<tr>'
    html += '<th>ID</th><th>Username</th><th>Email</th><th>CGPA</th><th>Branch</th><th>Gender</th><th>Role</th><th>Skills Count</th><th>Projects Count</th><th>Certifications Count</th><th>Latest ATS Score</th><th>Estimated Placement Odds</th>'
    html += '</tr>'
    
    for u in users:
        u_id = u['id']
        cursor.execute('SELECT COUNT(*) as count FROM skills WHERE user_id = ?', (u_id,))
        sc = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM projects WHERE user_id = ?', (u_id,))
        pc = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM certifications WHERE user_id = ?', (u_id,))
        cc = cursor.fetchone()['count']
        cursor.execute('SELECT ats_score FROM resumes WHERE user_id = ? ORDER BY analyzed_at DESC LIMIT 1', (u_id,))
        latest = cursor.fetchone()
        ats = latest['ats_score'] if latest else 'N/A'
        
        prob = 'N/A'
        if u['cgpa'] is not None:
            prob_calc = 35.0 + ((u['cgpa'] / 10.0) * 30.0) + min(15.0, sc * 3.0) + min(12.0, pc * 6.0) + min(8.0, cc * 4.0)
            prob = f"{min(99.0, round(prob_calc, 1))}%"
            
        role = 'Admin' if u['is_admin'] else 'Student'
        html += f'<tr>'
        html += f'<td>{u["id"]}</td><td>{u["username"]}</td><td>{u["email"]}</td>'
        html += f'<td>{u["cgpa"] if u["cgpa"] is not None else "N/A"}</td>'
        html += f'<td>{u["branch"] if u["branch"] else "N/A"}</td>'
        html += f'<td>{u["gender"] if u["gender"] else "N/A"}</td>'
        html += f'<td>{role}</td><td>{sc}</td><td>{pc}</td><td>{cc}</td><td>{ats}</td><td>{prob}</td>'
        html += '</tr>'
        
    html += '</table></body></html>'
    
    response = make_response(html)
    response.headers['Content-Disposition'] = 'attachment; filename=student_cohort_roster.xls'
    response.headers['Content-Type'] = 'application/vnd.ms-excel'
    return response

import os

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5001)),
        debug=False
    )