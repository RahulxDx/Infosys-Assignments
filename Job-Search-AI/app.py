from flask import Flask, request, render_template_string, redirect, url_for
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple HTML template for the app
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Search AI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: auto; }
        .results { background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; margin-top: 20px; }
        ul { list-style-type: disc; margin-left: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Job Search AI</h1>
        <p>Upload your CV in PDF format to analyze its content for job-relevant skills and get personalized job recommendations.</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="cv" accept=".pdf" required>
            <button type="submit">Submit</button>
        </form>
        {% if results %}
        <div class="results">
            <h2>Analysis Results:</h2>
            <p><strong>Extracted Skills:</strong></p>
            <ul>
                {% for skill in results.skills %}
                <li>{{ skill }} (Weight: {{ results.weights[skill] }})</li>
                {% endfor %}
            </ul>
            <h3>Suggested Job Titles:</h3>
            <ul>
                {% for job in results.jobs %}
                <li>{{ job }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# List of job-relevant skills with weights
SKILLS = {
    "Python": 10,
    "Flask": 8,
    "Machine Learning": 9,
    "Data Analysis": 7,
    "NLP": 8,
    "Deep Learning": 10,
    "SQL": 6,
    "Docker": 5,
    "Git": 6
}

# Mapping of skills to job titles
JOB_TITLES = {
    "Python": ["Python Developer", "Software Engineer"],
    "Flask": ["Backend Developer", "Web Developer"],
    "Machine Learning": ["ML Engineer", "Data Scientist"],
    "Data Analysis": ["Data Analyst", "BI Analyst"],
    "NLP": ["NLP Engineer", "AI Specialist"],
    "Deep Learning": ["AI Researcher", "Deep Learning Engineer"],
    "SQL": ["Database Administrator", "SQL Developer"],
    "Docker": ["DevOps Engineer", "Cloud Engineer"],
    "Git": ["Version Control Specialist", "Software Developer"]
}

# Function to extract text from PDF
def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# Function to analyze CV text for skills and suggest jobs based on weights
def analyze_cv(text):
    found_skills = {}
    for skill, weight in SKILLS.items():
        if skill.lower() in text.lower():
            found_skills[skill] = weight
    
    suggested_jobs = []
    for skill, weight in found_skills.items():
        for job_title in JOB_TITLES.get(skill, []):
            suggested_jobs.append(job_title)
    
    # Return skills found, their weights, and suggested job titles
    return {
        "skills": list(found_skills.keys()),
        "weights": found_skills,
        "jobs": suggested_jobs
    }

# Function to scrape jobs using Selenium (if you want to scrape jobs from Naukri)
def scrape_jobs(keywords):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    scraped_jobs = []
    try:
        for keyword in keywords:
            driver.get(f"https://www.naukri.com/{keyword}-jobs")
            job_elements = driver.find_elements(By.XPATH, '//a[contains(@class, "title")]')

            for job in job_elements[:5]:  # Limit to top 5 jobs per keyword
                job_title = job.text.strip()
                job_link = job.get_attribute('href')
                if job_title and job_link:
                    scraped_jobs.append({"title": job_title, "link": job_link})
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        driver.quit()

    return scraped_jobs

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE, results=None)

@app.route('/upload', methods=['POST'])
def upload():
    if 'cv' not in request.files:
        return redirect(url_for('index'))

    file = request.files['cv']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text and analyze CV
        text = extract_text_from_pdf(filepath)
        results = analyze_cv(text)

        # Optionally, scrape jobs based on extracted skills
        results["scraped_jobs"] = scrape_jobs(results["skills"])

        # Clean up uploaded file
        os.remove(filepath)

        return render_template_string(HTML_TEMPLATE, results=results)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
