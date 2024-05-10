import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import asyncio

app = Flask(__name__)
CORS(app)

# Function to read skills from file
def read_skills_from_file(file_path):
    with open(file_path, 'r') as file:
        skills = file.read().splitlines()
    return skills

# Read skills from file
skills_file_path = 'skills.txt'
try:
    skills_list = read_skills_from_file(skills_file_path)
except Exception as e:
    print(f"An error occurred while reading skills from file: {e}")
    skills_list = []

@app.route('/resume', methods=['POST'])
@cross_origin()
def handle_resume():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        
        # Debugging: Print the filename to understand what's being uploaded
        print("Uploaded Filename:", file.filename)
        
        # Adjusted condition: Remove or adjust this condition based on the actual filename
        if file and file.filename.endswith('.pdf'):
            # Extract text from the PDF content
            text = extract_text(file.stream)
            print("Extracted Text:", text)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            name = loop.run_until_complete(extract_name(text))
            contact_number = loop.run_until_complete(extract_contact_number_from_resume(text))
            email = loop.run_until_complete(extract_email_from_resume(text))
            skills = loop.run_until_complete(extract_skills_from_resume(text, skills_list))
            education = loop.run_until_complete(extract_education_from_resume(text))
            
            print("Name:", name)
            print("Contact Number:", contact_number)
            print("Email:", email)
            print("Skills:", skills)
            print("Education:", education)
            
            return jsonify({
                'name': name,
                'mail': email,
                'phone': contact_number,
                'skills': skills,
                'education': education
            })
        else:
            return jsonify({'error': 'Invalid file format. Only PDF files are allowed.'})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'})
    finally:
        if 'file' in locals():
            file.close()

async def extract_contact_number_from_resume(text):
    try:
        pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return None
    except Exception as e:
        print(f"An error occurred while extracting contact number: {e}")
        return None

async def extract_email_from_resume(text):
    try:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return None
    except Exception as e:
        print(f"An error occurred while extracting email: {e}")
        return None

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

async def extract_name(resume_text):
    try:
        nlp = spacy.load('en_core_web_sm')
        matcher = Matcher(nlp.vocab)
        patterns = [
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name followed by last name
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name followed by middle name followed by last name
            [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # First name followed by two middle names followed by last name
        ]

        for pattern in patterns:
            matcher.add('NAME', patterns=[pattern])

        doc = nlp(resume_text)
        matches = matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]
            return span.text

        return None
    except Exception as e:
        print(f"An error occurred while extracting name: {e}")
        return None

if __name__ == '__main__':  
    app.run(debug=True)
