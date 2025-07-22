import spacy
import calendar
import re
import spacy
import yaml
from dataclasses import dataclass
import sqlite3
from typing import List
from basemodel import *

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


class DBHandler:
    def __init__(self, db_name='university_info.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_name TEXT,
                heading TEXT,
                degree TEXT,
                year TEXT,
                deadline_type TEXT,
                deadline_date TEXT,
                notes TEXT
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admission_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_name TEXT,
                heading TEXT,
                degree TEXT,
                year TEXT,
                requirement_type TEXT,
                requirement_value TEXT,
                notes TEXT
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scholarships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_name TEXT,
                heading TEXT,
                scholarship_name TEXT,
                degree TEXT,
                amount TEXT,
                eligibility TEXT,
                application_deadline TEXT,
                notes TEXT
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS programs_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_name TEXT,
                heading TEXT,
                faculty TEXT,
                degree TEXT,
                program_name TEXT,
                duration TEXT,
                courses_list TEXT,
                notes TEXT
            );
        ''')

        self.conn.commit()


    def insert_deadlines(self, deadlines: List[ApplicationDeadline]):
        self.cursor.executemany('''
            INSERT INTO deadlines (university_name, heading, degree, year, deadline_type, deadline_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [(d.university_name, d.heading, d.degree, d.year, d.deadline_type, d.deadline_date, d.notes) for d in deadlines])
        self.conn.commit()

    def insert_requirements(self, requirements: List[AdmissionRequirement]):
        self.cursor.executemany('''
            INSERT INTO admission_requirements (university_name, heading, degree, year, requirement_type, requirement_value, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [(r.university_name, r.heading, r.degree, r.year, r.requirement_type, r.requirement_value, r.notes) for r in requirements])
        self.conn.commit()

    def insert_scholarships(self, scholarships: List[ScholarshipInfo]):
        self.cursor.executemany('''
            INSERT INTO scholarships (university_name, heading, scholarship_name, degree, amount, eligibility, application_deadline, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(s.university_name, s.heading, s.scholarship_name, s.degree, s.amount, s.eligibility, s.application_deadline, s.notes) for s in scholarships])
        self.conn.commit()

    def insert_programs(self, programs: List[ProgramInfo]):
        self.cursor.executemany('''
            INSERT INTO programs_courses (university_name, heading, faculty, degree, program_name, duration, courses_list, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(p.university_name, p.heading, p.faculty, p.degree, p.program_name, p.duration, p.courses_list, p.notes) for p in programs])
        self.conn.commit()


    def close(self):
        self.conn.close()
