import spacy
import calendar
import re
import spacy
import yaml
from dataclasses import dataclass
import sqlite3
from typing import List
import json
from urllib.parse import urlparse
from typing import List, Tuple
from spacy.tokens import Doc
from dataclasses import dataclass

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

@dataclass
class ApplicationDeadline:
    university_name: str
    heading: str
    degree: str
    year: str
    deadline_type: str
    deadline_date: str
    notes: str

    def __repr__(self):
        return (f"ApplicationDeadline(univ='{self.university_name}', heading='{self.heading}', "
                f"degree='{self.degree}', year='{self.year}', type='{self.deadline_type}', "
                f"date='{self.deadline_date}', notes='{self.notes[:20]}...')")


@dataclass
class AdmissionRequirement:
    university_name: str
    heading: str
    degree: str
    year: str
    requirement_type: str
    requirement_value: str
    notes: str

    def __repr__(self):
        return (f"AdmissionRequirement(univ='{self.university_name}', heading='{self.heading}', "
                f"degree='{self.degree}', year='{self.year}', type='{self.requirement_type}', "
                f"value='{self.requirement_value}', notes='{self.notes[:20]}...')")

@dataclass
class ScholarshipInfo:
    university_name: str
    heading: str
    scholarship_name: str
    degree: str
    amount: str
    eligibility: str
    application_deadline: str
    notes: str

    def __repr__(self):
        return (f"ScholarshipInfo(univ='{self.university_name}', heading='{self.heading}', "
                f"scholarship='{self.scholarship_name}', degree='{self.degree}', "
                f"amount='{self.amount}', eligibility='{self.eligibility[:20]}...', "
                f"deadline='{self.application_deadline}', notes='{self.notes[:20]}...')")

@dataclass
class ProgramInfo:
    university_name: str
    heading: str
    faculty: str
    degree: str
    program_name: str
    duration: str
    courses_list: str  # Can store JSON or CSV string
    notes: str

    def __repr__(self):
        return (f"ProgramInfo(univ='{self.university_name}', heading='{self.heading}', faculty='{self.faculty}', "
                f"degree='{self.degree}', program='{self.program_name}', duration='{self.duration}', "
                f"courses='{self.courses_list[:20]}...', notes='{self.notes[:20]}...')")
