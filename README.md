# AI Career & Placement Assistant

A professional, modern, and placement-ready ATS analyzer and career roadmap engine built to assist students and placement coordinators.

## Project Structure

### Frontend
- `templates/base.html`: The base HTML skeleton containing head tags, navbar, navigation tabs, and footer.
- `templates/login.html`: Authentic user login screen using clean, uniform card shadows and input fields.
- `templates/signup.html`: Create account screen for profile registration.
- `templates/dashboard.html`: The main analytical dashboard console displaying skill categories, placement metrics, and roadmap queries.

### Frontend Assets
- `static/css/style.css`: Core design system using flat, high-contrast `#0f172a` and `#1e293b` components.
- `static/js/main.js`: Interactive client controller script handling AJAX actions, profile additions, and dynamic gauges drawing.

### Backend
- `app.py`: Core controller application script managing authentication sessions, database connections, and resume-analyzers.
- `database.db`: Local SQLite relational database storing users, resume indices, and matched skillsets.
- `companies_seed.json`: Comprehensive database registry seeding 266 companies across 13 cities and 14 categories.
- `requirements.txt`: Backend dependency tracking file containing core pip modules.

## How to Run locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the application server:
   ```bash
   python3 app.py
   ```

3. Open your browser and navigate to `http://localhost:5001`. Log in with username `john_developer` and password `Password123` to test.
