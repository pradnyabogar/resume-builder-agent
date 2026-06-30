#!/usr/bin/env python3
"""
Resume Builder Agent — Option 2: Calculate ATS First, Then Create Resume
Two-step workflow: 1) Show match analysis, 2) User decides to build resume
"""

import os
import threading
import uuid
import time
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from resume_analyzer import load_docs_from_folder, compute_match, build_resume
from doc_generator import generate_word_resume
from web_reader import fetch_job_description

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "docs"
app.config["OUTPUT_FOLDER"] = "output"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

# In-memory job store for async progress tracking
jobs = {}
# Store match results separately so we can reuse them
match_cache = {}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_match_only(job_id: str, job_description: str):
    """Run match analysis only in a background thread."""
    try:
        jobs[job_id]["status"] = "loading_docs"
        jobs[job_id]["message"] = "Loading your documents..."
        resume_docs = load_docs_from_folder("docs")
        
        # Store resume_docs for later resume building
        match_cache[job_id] = {"resume_docs": resume_docs, "job_description": job_description}

        jobs[job_id]["status"] = "matching"
        jobs[job_id]["message"] = "Analyzing your match to this role..."
        match = compute_match(job_description, resume_docs)
        
        # Store match result
        match_cache[job_id]["match"] = match
        
        jobs[job_id]["status"] = "match_complete"
        jobs[job_id]["message"] = "Match analysis complete!"
        jobs[job_id]["match"] = match

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)


def build_resume_only(job_id: str):
    """Build resume using cached match data."""
    try:
        # Check if we have cached data
        if job_id not in match_cache:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = "Match data not found. Please calculate ATS score first."
            return
        
        cached = match_cache[job_id]
        job_description = cached["job_description"]
        resume_docs = cached["resume_docs"]
        match = cached.get("match", {})
        missing_kw = match.get("missing_keywords", [])
        
        jobs[job_id]["status"] = "waiting"
        jobs[job_id]["message"] = "Waiting 65 seconds for API rate limit to reset..."
        time.sleep(65)

        jobs[job_id]["status"] = "building"
        jobs[job_id]["message"] = "Building tailored resume targeting 85+ ATS..."
        result = build_resume(job_description, resume_docs, missing_kw)

        jobs[job_id]["status"] = "generating"
        jobs[job_id]["message"] = "Generating Word document..."
        tailored = result.get("tailored_resume", {})
        filepath = generate_word_resume(tailored, output_path="output")

        jobs[job_id]["status"] = "done"
        jobs[job_id]["message"] = "Resume ready!"
        jobs[job_id]["filename"] = os.path.basename(filepath)
        jobs[job_id]["ats_score"] = result.get("ats_score_estimate", "N/A")
        jobs[job_id]["suggestions"] = result.get("suggestions", [])
        
        # Keep match data in case user wants to see it again
        jobs[job_id]["match"] = match

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)


@app.route("/")
def index():
    return render_template("index_option2.html")


@app.route("/upload", methods=["POST"])
def upload_files():
    """Upload resume docs to the docs/ folder."""
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    uploaded = []
    files = request.files.getlist("files")
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            uploaded.append(filename)
    return jsonify({"uploaded": uploaded})


@app.route("/fetch-jd", methods=["POST"])
def fetch_jd():
    """Fetch job description from URL."""
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        text, warning = fetch_job_description(url)
        return jsonify({"text": text, "warning": warning})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/calculate-ats", methods=["POST"])
def calculate_ats():
    """Step 1: Calculate ATS score and show match analysis."""
    data = request.get_json()
    job_description = data.get("job_description", "").strip()
    if not job_description or len(job_description) < 50:
        return jsonify({"error": "Job description is too short"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "starting", "message": "Starting match analysis..."}

    thread = threading.Thread(target=calculate_match_only, args=(job_id, job_description))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/build-resume", methods=["POST"])
def build_resume_route():
    """Step 2: Build resume using existing match data."""
    data = request.get_json()
    job_id = data.get("job_id", "").strip()
    
    if not job_id:
        return jsonify({"error": "No job_id provided"}), 400
    
    if job_id not in match_cache:
        return jsonify({"error": "Match data not found. Please calculate ATS score first."}), 400
    
    # Update job status
    jobs[job_id] = {"status": "starting_resume", "message": "Starting resume build..."}
    
    thread = threading.Thread(target=build_resume_only, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    """Poll job status."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/download/<filename>")
def download(filename):
    """Download the generated resume."""
    filepath = os.path.join(app.config["OUTPUT_FOLDER"], secure_filename(filename))
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    print("\n  Resume Builder Agent - Option 2")
    print("  Two-Step Workflow: Calculate ATS → Build Resume")
    print("  Open http://localhost:5001 in your browser\n")
    app.run(debug=False, port=5001)
