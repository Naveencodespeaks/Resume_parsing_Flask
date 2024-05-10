import re
import spacy
from spacy.matcher import Matcher
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import asyncio
import pdfplumber
from docx import Document

app = Flask(__name__)
CORS(app)

# Function to read skills from file
def read_skills_from_file(file_path):
    """
    Reads skills from a text file and returns a list of skills.

    Args:
    - file_path (str): Path to the skills text file.

    Returns:
    - list: List of skills read from the file.
    """
    try:
        with open(file_path, 'r') as file:
            skills = file.read().splitlines()
        return skills
    except Exception as e:
        print(f"An error occurred while reading skills from file: {e}")
        return []

# Read skills from file
skills_file_path = 'skills.txt'
skills_list = read_skills_from_file(skills_file_path)

@app.route('/resume', methods=['POST'])
@cross_origin()
def handle_resume():
    """
    Handles the resume processing request.

    Returns:
    - JSON response: Extracted information from the resume or error message.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    try:
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file)
        else:
            return jsonify({'error': 'Invalid file format. Only PDF and DOCX files are allowed.'})

        name = extract_name(text)
        contact_number = extract_contact_number_from_resume(text)
        email = extract_email_from_resume(text)
        skills = extract_skills_from_resume(text, skills_list)
        education = extract_education_from_resume(text)

        missing_info = []
        extracted_info = {}
        if name is None:
            missing_info.append('name')
        else:
            extracted_info['name'] = name
        if contact_number is None:
            missing_info.append('contact_number')
        else:
            extracted_info['contact_number'] = contact_number
        if email is None:
            missing_info.append('email')
        else:
            extracted_info['email'] = email
        if not skills:
            missing_info.append('skills')
        else:
            extracted_info['skills'] = skills
        if not education:
            missing_info.append('education')
        else:
            extracted_info['education'] = education

        if missing_info:
            return jsonify({
                'error': f'Some information ({", ".join(missing_info)}) could not be extracted from the resume.',
                'missing_info': missing_info,
                'extracted_info': extracted_info
            })
        
        return jsonify({
            'extracted_info': extracted_info
        })
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing the resume.'})
    finally:
        if 'file' in locals():
            try:
                file.close()
            except Exception as e:
                print(f"An error occurred while closing the file: {e}")

def extract_text_from_pdf(file):
    """
    Extracts text content from a PDF file.

    Args:
    - file: PDF file object.

    Returns:
    - str: Extracted text content from the PDF.
    """
    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"An error occurred while extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file):
    """
    Extracts text content from a DOCX file.

    Args:
    - file: DOCX file object.

    Returns:
    - str: Extracted text content from the DOCX.
    """
    try:
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"An error occurred while extracting text from DOCX: {e}")
        return ""

def extract_contact_number_from_resume(text):
    """
    Extracts contact number from the resume text.

    Args:
    - text (str): Resume text content.

    Returns:
    - str: Extracted contact number.
    """
    try:
        pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return None
    except Exception as e:
        print(f"An error occurred while extracting contact number: {e}")
        return None

def extract_email_from_resume(text):
    """
    Extracts email address from the resume text.

    Args:
    - text (str): Resume text content.

    Returns:
    - str: Extracted email address.
    """
    try:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        match = re.search(pattern, text)
        if match:
            return match.group()
        return None
    except Exception as e:
        print(f"An error occurred while extracting email: {e}")
        return None

def extract_skills_from_resume(text, skills_list):
    """
    Extracts skills from the resume text.

    Args:
    - text (str): Resume text content.
    - skills_list (list): List of skills.

    Returns:
    - list: Extracted skills.
    """
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

def extract_education_from_resume(text):
    """
    Extracts education information from the resume text.

    Args:
    - text (str): Resume text content.

    Returns:
    - list: Extracted education information.
    """
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

def extract_name(resume_text):
    """
    Extracts name from the resume text.

    Args:
    - resume_text (str): Resume text content.

    Returns:
    - str: Extracted name.
    """
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

        return None
    except Exception as e:
        print(f"An error occurred while extracting name: {e}")
        return None

if __name__ == '__main__':  
    app.run(debug=True)
