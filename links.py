import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import asyncio

app = Flask(__name__)
CORS(app)

@app.route('/resume', methods=['POST'])
@cross_origin()
def handle_resume():
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
        skills = loop.run_until_complete(extract_skills_from_resume(text))
        education = loop.run_until_complete(extract_education_from_resume(text))
        github_link = loop.run_until_complete(extract_github_link(text))
        linkedin_link = loop.run_until_complete(extract_linkedin_link(text))
        
        print("Name:", name)
        print("Contact Number:", contact_number)
        print("Email:", email)
        print("Skills:", skills)
        print("Education:", education)
        print("GitHub Link:", github_link)
        print("LinkedIn Link:", linkedin_link)
        
        return jsonify({
            'name': name,
            'mail': email,
            'phone': contact_number,
            'skills': skills,
            'education': education,
            'github_link': github_link,
            'linkedin_link': linkedin_link
        })
    else:
        return jsonify({'error': 'Invalid file format. Only PDF files are allowed.'})


async def extract_contact_number_from_resume(text):
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

async def extract_email_from_resume(text):
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

async def extract_skills_from_resume(text):
    skills_list = ['python', 'data analysis', 'machine learning', 'communication', 'project management', 'deep learning', 'sql', 'tableau']
    skills = []
    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            skills.append(skill)
    return skills

async def extract_education_from_resume(text):
    education = []
    pattern = r"(?i)(?:B\.Tech|Bachelor\s(?:of)?\s(?:of)?\s(?:Technology|Science)|M\.Tech|Master\s(?:of)?\s(?:of)?\s(?:Technology|Science)|Ph\.D|Doctor(?:ate)?\s(?:of)?\s(?:Philosophy)?)(?:\s(?:in|of)\s[A-Za-z]+\s*)+"
    matches = re.findall(pattern, text)
    for match in matches:
        education.append(match.strip())
    return education

async def extract_github_link(text):
    pattern = r"\b(?:https?://)?(?:www\.)?github\.com/[^\s]+"
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

async def extract_linkedin_link(text):
    pattern = r"\b(?:https?://)?(?:www\.)?linkedin\.com/[^\s]+"
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

async def extract_name(resume_text):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # Capturing first, middle, and last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # Capturing first, middle, middle, and last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # Capturing first, middle, middle, middle, and last name
    ]

    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])

    doc = nlp(resume_text)
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text

    return None

if __name__ == '__main__':  
    app.run(debug=True)
