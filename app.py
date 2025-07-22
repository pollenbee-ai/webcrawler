from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import uuid
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import spacy
from markdownify import markdownify as md
from dateutil.parser import parse as dateparse
from datetime import date
from collections import defaultdict
from basemodel import *
from db.handler import DBHandler
from parser import SentenceParser
from flask_sqlalchemy import SQLAlchemy
import uuid
from db.database import *

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
app.secret_key = 'secretkey'  #Flask stores session data in the user's browser inside a cookie. This cookie is signed using the secret_key. Without app.secret_key, trying to access or set session['user'] would fail.

# Global cache
data_cache = {}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///university_info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Function to load data into cache
def load_data_to_cache(cache_key):
    data_cache[cache_key] = {
        'admission_requirements': [{
            'university_name': req.university_name,
            'heading': req.heading,
            'degree': req.degree,
            'year': req.year,
            'requirement_type': req.requirement_type,
            'requirement_value': req.requirement_value,
            'notes': req.notes
        } for req in AdmissionRequirement.query.all()],
        'application_process': [{
            'university_name': proc.university_name,
            'heading': proc.heading,
            'faculty': proc.faculty,
            'degree': proc.degree,
            'program_name': proc.program_name,
            'duration': proc.duration,
            'courses_list': proc.courses_list,
            'notes': proc.notes
        } for proc in ApplicationProcess.query.all()],
        'deadlines': [{
            'university_name': dl.university_name,
            'heading': dl.heading,
            'degree': dl.degree,
            'year': dl.year,
            'deadline_type': dl.deadline_type,
            'deadline_date': dl.deadline_date,
            'notes': dl.notes
        } for dl in Deadline.query.all()],
        'scholarships': [{
            'university_name': sch.university_name,
            'heading': sch.heading,
            'scholarship_name': sch.scholarship_name,
            'degree': sch.degree,
            'amount': sch.amount,
            'eligibility': sch.eligibility,
            'application_deadline': sch.application_deadline,
            'notes': sch.notes
        } for sch in Scholarship.query.all()]
    }

def is_valid_url(url):
    """Validate the URL format with a simplified regex."""
    regex = re.compile(
        r'^(https?:\/\/)?'  # Optional http:// or https://
        r'([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}'  # Domain with 2+ letter TLD
        r'(\/[a-zA-Z0-9\-\/]*)?$',  # Optional simple path
        re.IGNORECASE)
    return re.match(regex, url) is not None

def crawl_website(url, max_pages=10):
    print(url)
    try:
        visited = set()
        queue = deque([url])
        max_pages = int(max_pages) 

        # Set up retry strategy
        session = requests.Session()
        print(len(visited))

        # Crawl up to max_pages
        while queue and len(visited) < max_pages:
            current_url = queue.popleft()
            print("crawl_website>> ", current_url)

            if current_url in visited:
                print("current_url in visited>> ", current_url)
                continue         
            try:
                response = session.get(url, timeout=5)
            except Exception as e:
                print(f"[Error] Could not fetch {url}: {e}")
                return []

            if response.status_code != 200 or not response.text:
                raise Exception(f"Failed to fetch URL: {response.url} "
                    f"(Status: {response.status_code}, Empty Body: {not response.text})")

            response.raise_for_status()
            visited.add(current_url)
            print("len(visited)>> ", len(visited))

            soup = BeautifulSoup(response.text, 'html.parser')
            markdown_text = md(str(soup), heading_style="ATX")

            # text = soup.get_text(separator=' ', strip=True)
            # print(markdown_text)
            parser = SentenceParser('config.yaml', current_url)            

            parser.parse(markdown_text)
            print("Deadlines:", parser.deadlines)
            print("Requirements:", parser.requirements)
            print("Scholarships:", parser.scholarships)
            print("Programs:", parser.programs)

            print(parser.universityname)
            print(f"Requirements to insert >> requirements: {len(parser.requirements)}")
            print(f"Requirements to insert >> deadlines: {len(parser.deadlines)}")


            # with app.app_context():
            try:  
                deadlines = [
                Deadline(
                        university_name=parser.universityname,
                        heading=d.heading,
                        degree= d.degree,
                        year=d.year,
                        deadline_type=d.deadline_type,
                        deadline_date=d.deadline_date,
                        notes=d.notes
                    ) for d in parser.deadlines
                ]
                db.session.add_all(deadlines)

                # Insert admission requirements
                requirements = [
                    AdmissionRequirement(
                        university_name=parser.universityname,
                        heading=r.heading,
                        degree=r.degree,
                        year=r.year,
                        requirement_type=r.requirement_type,
                        requirement_value=r.requirement_value,
                        notes=r.notes
                    ) for r in parser.requirements
                ]
                db.session.add_all(requirements)

                # Insert scholarships
                scholarships = [
                    Scholarship(
                        university_name=parser.universityname,
                        heading=s.heading,
                        scholarship_name=s.scholarship_name,
                        degree=s.degree,
                        amount=s.amount,
                        eligibility=s.eligibility,
                        application_deadline=s.application_deadline,
                        notes=s.notes
                    ) for s in parser.scholarships
                ]
                db.session.add_all(scholarships)

                # Handle programs (convert dictionaries to ProgramInfo if needed)
                # programs = [
                #     ProgramInfo(**p) if isinstance(p, dict) else p
                #     for p in parser.programs
                # ]
                programs_models = [
                    ApplicationProcess(
                        university_name=parser.universityname,
                        heading=p.heading,
                        faculty=p.faculty,
                        degree=p.degree,
                        program_name=p.program_name,
                        duration=p.duration,
                        courses_list=p.courses_list,
                        notes=p.notes
                    ) for p in parser.programs
                ]
                db.session.add_all(programs_models)

                # Commit all changes
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error inserting data: {e}")
                raise

            # db = DBHandler()

            # db.insert_deadlines(parser.deadlines)
            # db.insert_requirements(parser.requirements)
            # db.insert_scholarships(parser.scholarships)
            # db.insert_programs(parser.programs)

            # db.close()

            # Follow links within the same domain
            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href'])
                if urlparse(full_url).netloc == urlparse(url).netloc and full_url not in visited:
                    queue.append(full_url)

        # Cache and return extracted data
        cache_key = str(uuid.uuid4())   
        data_cache[cache_key] = parser.get_extracted_data()
        return {"cache_key": cache_key}, None
    except Exception as e:
        print(f"\n\nException >>> {e} \n\n")
        cache_key = str(uuid.uuid4())
        data_cache[cache_key] = ""
        error_msg = f"Failed to crawl {url}: {str(e)}"
        if isinstance(e, requests.Timeout):
            error_msg = "Request timed out. No data extracted."
        elif isinstance(e, requests.HTTPError):
            if e.response.status_code == 404:
                error_msg = "Website not found (404). No data extracted."
            elif e.response.status_code == 403:
                error_msg = "Access denied by the website. No data extracted."
            elif e.response.status_code == 429:
                error_msg = "Too many requests. No data extracted."
            else:
                error_msg = f"HTTP error {e.response.status_code}. No data extracted."
        return {"cache_key": cache_key}, error_msg

@app.route('/')
def dashboard():
    if 'crawled_data' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/data/<category>')
def get_data(category):
    if 'crawled_data' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    cache_key = session.get('crawled_data', {}).get('cache_key')
    if not cache_key or cache_key not in data_cache:
        with app.app_context():
            data_cache[cache_key] = {
                'admission_requirements': [{
                    'university_name': r.university_name, 'heading': r.heading, 'degree': r.degree,
                    'year': r.year, 'requirement_type': r.requirement_type, 'requirement_value': r.requirement_value,
                    'notes': r.notes
                } for r in AdmissionRequirement.query.all()],
                'application_process': [{
                    'university_name': p.university_name, 'heading': p.heading, 'faculty': p.faculty,
                    'degree': p.degree, 'program_name': p.program_name, 'duration': p.duration,
                    'courses_list': p.courses_list, 'notes': p.notes
                } for p in ApplicationProcess.query.all()],
                'deadlines': [{
                    'university_name': d.university_name, 'heading': d.heading, 'degree': d.degree,
                    'year': d.year, 'deadline_type': d.deadline_type, 'deadline_date': d.deadline_date,
                    'notes': d.notes
                } for d in Deadline.query.all()],
                'scholarships': [{
                    'university_name': s.university_name, 'heading': s.heading, 'scholarship_name': s.scholarship_name,
                    'degree': s.degree, 'amount': s.amount, 'eligibility': s.eligibility,
                    'application_deadline': s.application_deadline, 'notes': s.notes
                } for s in Scholarship.query.all()]
            }
    data = data_cache.get(cache_key, {})
    if category in data:
        return jsonify(data[category])
    return jsonify([]), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            url = request.form['url'].strip()
            max_pages = request.form['max_pages']
            session['crawled_data'] = {'cache_key': str(uuid.uuid4())}
            crawl_website(url, max_pages=int(max_pages))  # Call crawler
            load_data_to_cache(session['crawled_data']['cache_key'])
            return redirect('/')
        except KeyError as e:
            return render_template('login.html', error='Please provide both URL and max pages.')
        except Exception as e:
            return render_template('login.html', error=f'Error: {str(e)}')
    return render_template('login.html', error=None)

@app.route('/')
def index():
    if 'crawled_data' not in session:
        return redirect('/login')
    return app.send_static_file('dashboard.html')

@app.route('/logout')
def logout():
    cache_key = session.get('crawled_data', {}).get('cache_key')
    if cache_key in data_cache:
        del data_cache[cache_key]
    session.pop('crawled_data', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True, use_reloader=False)