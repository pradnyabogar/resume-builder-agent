"""
Quick test script to run the agent with a hardcoded job URL
"""
import os
import sys
from resume_analyzer import load_docs_from_folder, compute_match, build_resume
from web_reader import fetch_job_description
from doc_generator import generate_word_resume

# Test with Microsoft TPM job
JOB_URL = "https://jobs.careers.microsoft.com/global/en/job/1782990/Senior-Technical-Program-Manager"

print("=" * 60)
print("   Testing Resume Builder Agent")
print("=" * 60)

# Step 1: Load docs
print("\n[1/4] Loading documents...")
resume_docs = load_docs_from_folder("docs")

if not resume_docs.strip():
    print("[error] No documents loaded. Check ./docs/ folder")
    sys.exit(1)

# Step 2: Fetch job description
print(f"\n[2/4] Fetching job from: {JOB_URL}")
try:
    job_description = fetch_job_description(JOB_URL)
    print(f"  ✓ Loaded {len(job_description)} chars")
    if len(job_description) < 100:
        print("[warn] Job description seems too short. Using it anyway for testing...")
except Exception as e:
    print(f"[error] Could not fetch job: {e}")
    sys.exit(1)

# Step 3: Compute match
print("\n[3/4] Computing match score...")
print("  (waiting 5 seconds before GPT call...)")
import time
time.sleep(5)

try:
    match_result = compute_match(job_description, resume_docs)
    print("\n" + "=" * 60)
    print("   MATCH ANALYSIS")
    print("=" * 60)
    print(f"  Match:          {match_result['match_pct']}%")
    print(f"  Rating:         {match_result['rating']}")
    print(f"  Recommendation: {match_result['recommendation']}")
    print(f"\n  Summary:")
    print(f"    {match_result['summary']}")
    print(f"\n  Strengths:")
    for s in match_result.get('strengths', [])[:5]:
        print(f"    ✓ {s}")
    print(f"\n  Gaps:")
    for g in match_result.get('gaps', [])[:5]:
        print(f"    ✗ {g}")
    print(f"\n  Missing Keywords:")
    print(f"    {', '.join(match_result.get('missing_keywords', [])[:15])}")
    print("=" * 60)
    
    # Auto-proceed if match is decent
    if match_result['match_pct'] < 40:
        print("\n[warn] Low match score. Proceeding anyway for testing...")
    
    missing_kw = match_result.get('missing_keywords', [])
    
except Exception as e:
    print(f"[error] Match analysis failed: {e}")
    sys.exit(1)

# Step 4: Build resume
print("\n[4/4] Building tailored resume...")
print("  (waiting 65 seconds before next GPT call to avoid rate limit...)")
time.sleep(65)

try:
    result = build_resume(job_description, resume_docs, missing_kw)
    
    print(f"\n  ✓ Resume built")
    print(f"  Estimated ATS Score: {result.get('ats_score_estimate', 'N/A')}")
    
    # Generate Word doc
    resume_data = result.get('tailored_resume', {})
    filepath = generate_word_resume(resume_data, "output")
    
    print(f"\n" + "=" * 60)
    print(f"   SUCCESS!")
    print("=" * 60)
    print(f"  Resume saved: {filepath}")
    print(f"  ATS Score:    {result.get('ats_score_estimate', 'N/A')}")
    
    # Show experience bullet count
    experience = resume_data.get('experience', [])
    if experience:
        print(f"\n  Experience bullets:")
        for job in experience[:3]:  # Show first 3 roles
            bullets = len(job.get('bullets', []))
            print(f"    {job.get('title', 'Unknown')}: {bullets} bullets")
    
    # Show skills count
    skills = resume_data.get('skills', [])
    print(f"\n  Skills: {len(skills)} listed")
    if skills:
        print(f"    {', '.join(skills[:10])}{'...' if len(skills) > 10 else ''}")
    
    print("=" * 60)
    
except Exception as e:
    print(f"[error] Resume building failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
