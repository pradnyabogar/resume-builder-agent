#!/usr/bin/env python3
"""
Resume Builder Agent — Flask Web UI
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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_agent(job_id: str, job_description: str):
    """Run match + resume build in a background thread."""
    try:
        jobs[job_id]["status"] = "loading_docs"
        jobs[job_id]["message"] = "Loading your documents..."
        resume_docs = load_docs_from_folder("docs")

        jobs[job_id]["status"] = "matching"
        jobs[job_id]["message"] = "Analysing your match to this role..."
        match = compute_match(job_description, resume_docs)
        jobs[job_id]["match"] = match

        jobs[job_id]["status"] = "waiting"
        jobs[job_id]["message"] = "Waiting 65 seconds for API rate limit to reset..."
        time.sleep(65)

        jobs[job_id]["status"] = "building"
        jobs[job_id]["message"] = "Building tailored resume targeting 85+ ATS..."
        missing_kw = match.get("missing_keywords", [])
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

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


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


@app.route("/run", methods=["POST"])
def run():
    """Start the agent in a background thread."""
    data = request.get_json()
    job_description = data.get("job_description", "").strip()
    if not job_description or len(job_description) < 50:
        return jsonify({"error": "Job description is too short"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "starting", "message": "Starting..."}

    thread = threading.Thread(target=run_agent, args=(job_id, job_description))
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
    print("\n  Resume Builder Agent")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(debug=False, port=5000)
