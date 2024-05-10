import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import asyncio

app = Flask(__name__)
CORS(app)

# Read skills from a text file
def read_skills_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            skills = file.read().splitlines()
        return skills
    except Exception as e:
        print(f"An error occurred while reading skills from file: {e}")
        return []

# Endpoint handler for processing resumes
@app.route('/resume', methods=['POST'])
@cross_origin()
def handle_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    try:
        if file and file.filename.endswith('.pdf'):
            text = extract_text(file.stream)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            name = loop.run_until_complete(extract_name(text))
            contact_number = loop.run_until_complete(extract_contact_number_from_resume(text))
            email = loop.run_until_complete(extract_email_from_resume(text))
            skills_list = read_skills_from_file("skills.txt")
            skills = loop.run_until_complete(extract_skills_from_resume(text, skills_list))
            education = loop.run_until_complete(extract_education_from_resume(text))
            
            return jsonify({
                'name': name if name else '',
                'mail': email if email else '',
                'phone': contact_number if contact_number else '',
                'skills': skills if skills else [],
                'education': education if education else []
            })
        else:
            return jsonify({'error': 'Invalid file format. Only PDF files are allowed.'})
    except Exception as e:
        print(f"An error occurred while handling the resume: {e}")
        return jsonify({'error': 'An error occurred while processing the resume.'})
    finally:
        if 'file' in locals():
            try:
                file.close()
            except Exception as e:
                print(f"An error occurred while closing the file: {e}")

# Asynchronously extract contact number from resume text
async def extract_contact_number_from_resume(text):
    try:
        pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return ''
    except Exception as e:
        print(f"An error occurred while extracting contact number: {e}")
        return ''

# Asynchronously extract email from resume text
async def extract_email_from_resume(text):
    try:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return ''
    except Exception as e:
        print(f"An error occurred while extracting email: {e}")
        return ''

# Asynchronously extract skills from resume text
async def extract_skills_from_resume(text, skills_list):
    try:
        skills = []
        for skill in skills_list:
            pattern = r"\b{}\b".format(re.escape(skill))
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                skills.append(skill)
        return skills
    except Exception as e:
        print(f"An error occurred while extracting skills: {e}")
        return []

# Asynchronously extract education from resume text
async def extract_education_from_resume(text):
    try:
        education = []
        pattern = r"(?i)(?:Bsc|\bB\.\w+|\bM\.\w+|\bPh\.D\.\w+|\bBachelor(?:'s)?|\bMaster(?:'s)?|\bPh\.D|\bB\.Tech)\s(?:\w+\s)*\b(?:be\s)?\w+"
        matches = re.findall(pattern, text)
        for match in matches:
            education.append(match.strip())
        return education
    except Exception as e:
        print(f"An error occurred while extracting education: {e}")
        return []

# Asynchronously extract name from resume text
async def extract_name(resume_text):
    try:
        nlp = spacy.load('en_core_web_sm')
        matcher = Matcher(nlp.vocab)
        patterns = [
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  
        ]

        for pattern in patterns:
            matcher.add('NAME', patterns=[pattern])

        doc = nlp(resume_text)
        matches = matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]
            return span.text

        return ''
    except Exception as e:
        print(f"An error occurred while extracting name: {e}")
        return ''

if __name__ == '__main__':  
    app.run(debug=True)
