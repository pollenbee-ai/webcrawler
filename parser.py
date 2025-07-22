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
from markdown import markdown
from bs4 import BeautifulSoup, Tag
from collections import defaultdict
import hashlib
import pycountry

import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('wordnet')
from spacy.matcher import PhraseMatcher

from basemodel import *

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

class SentenceParser:
    def __init__(self, category_keywords_path, university_url):
        self.category_keywords = self.load_keywords(category_keywords_path)
        self.classified = {cat: {} for cat in self.category_keywords}
        self.deadlines = []
        self.requirements = []
        self.scholarships = []
        self.programs = []
        self.universityname = self.extract_university_name(university_url)
        self.processed_sentences_hash = set()
        self.patterns = [nlp.make_doc(text) for text in self.category_keywords["programs_courses"]]
        self.matcher = PhraseMatcher(nlp.vocab, attr="LOWER") 
        self.matcher.add("DEGREE", self.patterns)

    
    def compute_sentence_hash(self, sentence: str) -> str:
        return hashlib.sha256(sentence.strip().lower().encode('utf-8')).hexdigest()

    def get_extracted_data(self):
        return {
            "deadlines": self.deadlines,
            "admission_requirements": self.requirements,
            "scholarships": self.scholarships,
            "programs_courses": self.programs
        }

    def is_country(self, name: str) -> bool:
        parts  = name.split() if ' ' in name else [name]
        for part in parts:
            try:
                pycountry.countries.lookup(part)
                return True
            except LookupError:
                continue
        return False


    def extract_university_name(self, url: str) -> str:
        """
        Extracts university name from a given URL.
        Example: https://www.citystgeorges.ac.uk -> Citystgeorges
        """
        domain = urlparse(url).netloc.lower()
        
        # Remove subdomains like www, admissions, etc.
        parts = domain.split('.')
        parts = [p for p in parts if p not in ['www', 'edu', 'ac', 'in', 'uk', 'org', 'com', 'net']]

        # Special handling for short domains like mit.edu or ox.ac.uk
        if len(parts) == 1:
            return parts[0].upper()

        # Combine remaining parts and capitalize
        name = ' '.join(parts)
        print(name)
        return name.replace('-', ' ').title()

    def load_keywords(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def normalize_dates(self, text):
        text = re.sub(r'\b(post|pre|mid|early|late)[-–](January|February|March|April|May|June|July|August|September|October|November|December)\b',
                    r'\1 \2', text, flags=re.IGNORECASE)
        return text
    
    def parse_markdown(self, markdown_text):
        html = markdown(markdown_text)
        soup = BeautifulSoup(html, 'html.parser')

        sections = {}
        current_header = None

        elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'ul', 'ol', 'li', 'div'])
        i = 0

        while i < len(elements):
            el = elements[i]
            tag = el.name
            text = el.get_text(separator=' ', strip=True)

            # Section heading
            if tag in ['h1', 'h2']:
                current_header = text.lower().replace(" ", "_")
                sections.setdefault(current_header, [])

            # Subheading + group following p/li/ul
            elif tag in ['h3', 'h4', 'h5'] and current_header:
                combined = text
                j = i + 1
                while j < len(elements) and elements[j].name in ['p', 'ul', 'ol', 'li']:
                    combined += " " + elements[j].get_text(separator=' ', strip=True)
                    j += 1
                sections[current_header].append(combined)
                i = j - 1  # skip processed elements

            # Plain paragraphs and list items
            elif tag in ['p', 'li'] and current_header:
                if text:
                    sections[current_header].append(text)

            # Combine all <li> in a <ul>/<ol>
            elif tag in ['ul', 'ol'] and current_header:
                items = [li.get_text(separator=' ', strip=True) for li in el.find_all('li')]
                if items:
                    sections[current_header].append(" ".join(items))

            # Treat <div> as a block (regardless of nested tags)
            elif tag == 'div' and current_header:
                if text:
                    sections[current_header].append(text)

            i += 1

        return sections
        
    def is_semantically_related(self, sentence: str, target_concept: str = "requirement") -> bool:
            lowered = sentence.lower()
            tokens = word_tokenize(lowered)

            for word in tokens:
                word_synsets = wn.synsets(word)
                target_synsets = wn.synsets(target_concept)

                for word_syn in word_synsets:
                    for target_syn in target_synsets:
                        if word_syn == target_syn:
                            return True
                        if target_syn in word_syn.hypernyms() or word_syn in target_syn.hypernyms():
                            return True
                        # Check deeper hypernym paths
                        if target_syn in word_syn.closure(lambda s: s.hypernyms()):
                            return True
            return False
    
    def classify_sentence(self, sentence: str) -> str:
        doc = nlp(sentence.lower())
        ents = {ent.label_ for ent in doc.ents}
        tokens = [token.text for token in doc]

        # Check keywords first
        for category, keywords in self.category_keywords.items():
            if any(kw in sentence.lower() for kw in keywords):
                return category

        # Using NER-based rules
        has_org = "ORG" in ents
        has_money_or_percent_or_product_or_norp = any(label in ents for label in ["MONEY", "PERCENT", "PRODUCT", "NORP"])
        has_product_or_loc_or_cardinal = any(label in ents for label in ["PRODUCT", "LOC", "CARDINAL"])
        has_date_related = any(label in ents for label in ["DATE", "TIME", "ORDINAL", "CARDINAL"])

        if has_org and has_money_or_percent_or_product_or_norp:
            return "scholarships"
        elif has_money_or_percent_or_product_or_norp:
            return "scholarships"
        elif has_org and has_product_or_loc_or_cardinal:
            return "programs_courses"
        elif has_date_related:
            return "deadlines"
        else:
            return "admission_requirements"

    def parse(self, markdown_sentences):
        sections = self.parse_markdown(markdown_sentences)
        # print(sections)
        for heading, content_list in sections.items():
            for sentence in content_list:
                doc = nlp(sentence)
                for sent in doc.sents:
                    sent_text = sent.text.strip()
                    
                    category = self.classify_sentence(sent_text)
                    if heading not in self.classified[category]:
                        self.classified[category][heading] = []
                    self.classified[category][heading].append(sent_text)

                # self.classified[category].append(sentence)
        print(json.dumps(self.classified, indent=2))
        print("-"*30)

        with open("classified.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.classified, indent=2, ensure_ascii=False))

        try:
            self.extract_application_deadlines(self.classified["deadlines"])
            self.extract_programs_courses(self.classified["programs_courses"])
            self.extract_scholarship(self.classified["scholarships"])
            self.extract_admission_requirements(self.classified["admission_requirements"])
        except Exception as e:
            print(e)

    def extract_programs_courses(self, programs_courses_map: dict) -> List[ProgramInfo]:        
        for heading, programs_courses in programs_courses_map.items():
            for sent_text_base in programs_courses:
                sent_text_base = sent_text_base.strip()
                markdown_hash_split_text = sent_text_base.split("##")
                for sent_text in markdown_hash_split_text:
                    sent_text = sent_text.strip()
                    sent_text = heading + "\n\n" + sent_text

                    sent_hash = self.compute_sentence_hash(sent_text)            
                    if sent_hash in self.processed_sentences_hash:
                        continue  # Skip already processed sentences
                    
                    sent_doc = nlp(sent_text)  
                    orgs = [ent.text for ent in sent_doc.ents if ent.label_ == "ORG"]

                    dates = [ent.text for ent in sent_doc.ents if ent.label_ in ["DATE", "TIME", "YEAR"]]

                    programs = [chunk.text for chunk in sent_doc.noun_chunks if "program" in chunk.text.lower() or "course" in chunk.text.lower()]
                    program_name = programs[0] if programs else "Unknown Program"
                    duration = dates[0] if dates else "Unknown Duration"
                    
                    def extract_degrees(text: str):
                        doc = nlp(text)
                        matches = self.matcher(doc)
                        matched_degrees = [doc[start:end].text for match_id, start, end in matches]
                        return matched_degrees
                    degree = extract_degrees(sent_text)                    
                    max_len_degree = ""
                    if not degree:
                        continue
                    else:
                        max_len_degree = max(degree, key=len)
                    
                    if max_len_degree != "":
                        self.programs.append(ProgramInfo(
                            university_name=self.universityname,
                            heading=heading,
                            faculty="Unknown Faculty",              # Can improve with keyword matching
                            degree=max_len_degree,
                            program_name=program_name,
                            duration=duration,
                            courses_list="[]",                     
                            notes=sent_text                         # Store full sentence as notes
                        ))

    def extract_application_deadlines(self, deadline_sentences_map):
        for heading, deadline_sentenses in deadline_sentences_map.items():
            for sent_text_base in deadline_sentenses:
                sent_text_base = sent_text_base.strip()
                markdown_hash_split_text = sent_text_base.split("##")
                for sent_text in markdown_hash_split_text:
                    sent_hash = self.compute_sentence_hash(sent_text)            
                    if sent_hash in self.processed_sentences_hash:
                        continue  # Skip already processed sentences
                    
                    sent_text = heading + "\n\n" + sent_text
                    sent_text = self.normalize_dates(sent_text)
                    sent_doc = nlp(sent_text)

                    # Extract ORGs and filter out countries
                    orgs = {
                        ent.text.strip()
                        for ent in sent_doc.ents
                        if ent.label_ == "ORG" and not self.is_country(ent.text.strip())
                    }

                    # Extract dates as a set
                    dates = {
                        ent.text.strip()
                        for ent in sent_doc.ents
                        if ent.label_ in ["DATE", "TIME", "YEAR"]
                    }

                    def is_duplicate(new_item, existing_list):
                        """
                        Check if a new ApplicationDeadline already exists in the list 
                        based on university_name, degree, deadline_type, and deadline_date.
                        """
                        return any(
                            d.university_name == new_item.university_name and
                            d.degree == new_item.degree and
                            d.deadline_type == new_item.deadline_type and
                            d.deadline_date == new_item.deadline_date
                            for d in existing_list
                        )

                    if dates and orgs:
                        org_str = "| ".join(sorted(orgs))
                        date_str = "| ".join(sorted(dates))

                        # for date in dates:
                        #     for org in orgs:
                        newobj = ApplicationDeadline(
                            university_name=self.universityname,
                            degree=org_str,
                            heading=heading,
                            year="Unknown Year",
                            deadline_type="Application Deadline",
                            deadline_date=date_str,
                            notes=sent_text
                        )
                        if not self.is_country(newobj.degree):
                            if not is_duplicate(newobj, self.deadlines):
                                self.deadlines.append(newobj)

                        # else:   #REMOVING TO AVOID JUNK DATAs
                        #     # print("Noun Chunks:")
                        #     noun_chunk = ""
                        #     for chunk in sent_doc.noun_chunks:
                        #         if any(token.ent_type_ in ["DATE", "TIME", "YEAR"] for token in chunk):
                        #             continue
                        #         else:
                        #             noun_chunk += chunk.text + " "
                        #             # print("-", chunk.text)
                        #     noun_chunks_str = noun_chunk.strip()

                        #     self.deadlines.append(ApplicationDeadline(
                        #                 university_name=self.universityname,
                        #                 heading= heading,
                        #                 degree=noun_chunks_str,
                        #                 year="Unknown Year",
                        #                 deadline_type="Application Deadline",
                        #                 deadline_date=date,
                        #                 notes=sent_text))

    def extract_money_and_duration(self, doc: Doc):
        """Returns tuples: (amount, duration like 'per year' '2 euro' etc)"""
        result = set()

        for i, token in enumerate(doc):
            if token.is_currency:
                next_token = doc[i + 1] if i + 1 < len(doc) else None
                if next_token and (next_token.like_num or next_token.text.replace(",", "").isdigit()):
                    money = f"{token.text}{next_token.text}"
                    duration = ""

                    # Append money unit 
                    if i + 2 < len(doc) and doc[i + 2].text.lower() in ["lakh", "billion", "euro", "pound", "million", "thousand", "crore"]:
                        money += f" {doc[i + 2].text}"
                        if i + 3 < len(doc) and doc[i + 3].text in ["per", "a"]:
                            if i + 4 < len(doc):
                                duration = f"{doc[i + 3].text} {doc[i + 4].text}"
                                money += f" {duration}"
                    else:
                        # look for duration
                        if i + 2 < len(doc) and doc[i + 2].text in ["per", "a"]:
                            if i + 3 < len(doc):
                                duration = f"{doc[i + 2].text} {doc[i + 3].text}"
                                money += f" {duration}"

                    result.add((money.strip(), duration.strip()))

        # only if result is empty
        if not result:
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    result.add((ent.text.strip(), ""))

        return list(result)

    

                    # for org in orgs:
                    #     for amount, duration in money_tuples:
                    #         for degree in degrees:
                    #             for scholarship_name in scholarship_names:
                    #                 if scholarship_name == "Unnamed Scholarship":
                    #                     continue  # Skip unclear names

                    #                 self.scholarships.append(ScholarshipInfo(
                    #                     university_name=self.universityname,
                    #                     heading=heading,
                    #                     scholarship_name=scholarship_name,
                    #                     degree=degree,
                    #                     amount=amount,
                    #                     eligibility=sent_text,
                    #                     application_deadline=duration,
                    #                     notes=sent_text
                    #                 ))
    
    def extract_admission_requirements(self, admission_requirement_sentences_map: dict) -> List[AdmissionRequirement]:
        req_keywords = set(k.lower() for k in self.category_keywords.get("admission_requirements", []))
        degree_keywords = set(k.lower() for k in self.category_keywords.get("programs_courses", []))

        for heading, sentences in admission_requirement_sentences_map.items():
            for sent_text_base in sentences:
                sent_text_base = sent_text_base.strip()
                markdown_hash_split_text = sent_text_base.split("##")
                for sent_text in markdown_hash_split_text:
                    sent_text = sent_text.strip()
                    sent_text = heading + "\n\n" + sent_text

                    sent_hash = self.compute_sentence_hash(sent_text)
                    if sent_hash in self.processed_sentences_hash:
                        continue

                    sent_text = self.normalize_dates(sent_text)
                    doc = nlp(sent_text)

                    degrees = {
                        ent.text.strip()
                        for ent in doc.ents
                        if ent.label_ == "EDUCATION"
                    }

                    year = next((ent.text.strip() for ent in doc.ents if ent.label_ in ["DATE", "TIME", "YEAR"]), "")

                    # Fallback for degree using keyword matching
                    if not degrees:
                        for token in doc:
                            if token.text.lower() in degree_keywords:
                                degrees = {token.text.strip()}
                                break

                    # Extract requirement_type
                    matched_requirements = {
                        token.text.strip()
                        for token in doc
                        if token.text.lower() in req_keywords
                    }

                    requirement_type = next(iter(matched_requirements), "")
                    requirement_value = ""

                    if requirement_type:
                        for token in doc:
                            if token.text.lower() == requirement_type.lower():
                                prev_token = doc[token.i - 1].text if token.i > 0 else ""
                                next_token = doc[token.i + 1].text if token.i + 1 < len(doc) else ""

                                if prev_token.isdigit():
                                    requirement_value = f"{prev_token} {token.text}"
                                elif next_token.isdigit():
                                    requirement_value = f"{token.text} {next_token}"
                                else:
                                    requirement_value = token.text
                                break

                    # Default to empty if still unset
                    degrees = degrees or {""}
                    requirement_type = requirement_type or ""
                    requirement_value = requirement_value or ""

                    for degree in degrees:
                        if degree == "" and year == "":
                            continue
                        self.requirements.append(AdmissionRequirement(
                            university_name=self.universityname,
                            heading=heading,
                            degree=degree,
                            year=year,
                            requirement_type=requirement_type,
                            requirement_value=requirement_value,
                            notes=sent_text
                        ))