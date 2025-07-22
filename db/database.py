from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Database models
class AdmissionRequirement(db.Model):
    __tablename__ = 'admission_requirements'
    id = db.Column(db.Integer, primary_key=True)
    university_name = db.Column(db.String)
    heading = db.Column(db.String)
    degree = db.Column(db.String)
    year = db.Column(db.String)
    requirement_type = db.Column(db.String)
    requirement_value = db.Column(db.String)
    notes = db.Column(db.Text)

class ApplicationProcess(db.Model):
    __tablename__ = 'programs_courses'
    id = db.Column(db.Integer, primary_key=True)
    university_name = db.Column(db.String)
    heading = db.Column(db.String)
    faculty = db.Column(db.String)
    degree = db.Column(db.String)
    program_name = db.Column(db.String)
    duration = db.Column(db.String)
    courses_list = db.Column(db.Text)
    notes = db.Column(db.Text)

class Deadline(db.Model):
    __tablename__ = 'deadlines'
    id = db.Column(db.Integer, primary_key=True)
    university_name = db.Column(db.String)
    heading = db.Column(db.String)
    degree = db.Column(db.String)
    year = db.Column(db.String)
    deadline_type = db.Column(db.String)
    deadline_date = db.Column(db.String)
    notes = db.Column(db.Text)

class Scholarship(db.Model):
    __tablename__ = 'scholarships'
    id = db.Column(db.Integer, primary_key=True)
    university_name = db.Column(db.String)
    heading = db.Column(db.String)
    scholarship_name = db.Column(db.String)
    degree = db.Column(db.String)
    amount = db.Column(db.String)
    eligibility = db.Column(db.Text)
    application_deadline = db.Column(db.String)
    notes = db.Column(db.Text)
