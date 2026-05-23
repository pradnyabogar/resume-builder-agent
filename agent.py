#!/usr/bin/env python3
"""
Job Application Agent
---------------------
1. Reads your docs from ./docs/
2. Asks for a job posting URL
3. Fetches the job description
4. Smart comparison — shows match % and gaps
5. You decide whether to proceed
6. Builds a tailored Word resume targeting 85+ ATS in ./output/
"""

import os
import sys
from dotenv import load_dotenv

from web_reader import fetch_job_description
from resume_analyzer import load_docs_from_folder, compute_match, build_resume
from doc_generator import generate_word_resume

load_dotenv()


def check_env():
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[error] OPENAI_API_KEY not set.")
        print("  Copy .env.example to .env and add your OpenAI key.\n")
        sys.exit(1)


def print_banner():
    print("\n" + "=" * 60)
    print("   Job Application Agent")
    print("=" * 60)


def step_get_url() -> str:
    """Ask for a job posting URL."""
    print("\n[1/4] Paste the job posting URL and press Enter:")
    url = input("  > ").strip()
    if not url:
        print("[error] No URL provided. Exiting.")
        sys.exit(1)
    return url


def step_fetch_jd(job_url: str) -> str:
    """Fetch job description from URL with manual paste fallback."""
    print(f"\n[2/4] Fetching job description...")
    try:
        text, warning = fetch_job_description(job_url)
    except RuntimeError as e:
        print(f"  [error] {e}")
        text, warning = "", str(e)

    if warning:
        print(f"  ⚠️  {warning}")

    if len(text.strip()) < 100:
        print("\n  Could not extract enough text from that URL.")
        print("  Paste the job description below. Type END on a new line when done:\n")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        text = "\n".join(lines)
        if len(text.strip()) < 50:
            print("[error] Not enough text. Exiting.")
            sys.exit(1)
        print(f"  ✓ Using pasted description ({len(text)} chars)")
    else:
        print(f"  ✓ Fetched {len(text)} chars")
        print(f"  Preview: {text[:200].replace(chr(10), ' ')}...")

    return text


def step_show_match(job_description: str, resume_docs: str) -> tuple[bool, list]:
    """
    Smart semantic comparison using GPT.
    Shows match %, strengths, gaps. Asks user to proceed.
    Returns (proceed: bool, missing_keywords: list).
    """
    print(f"\n[3/4] Analysing your match to this role...")

    try:
        match = compute_match(job_description, resume_docs)
    except RuntimeError as e:
        print(f"  [error] {e}")
        print("  Skipping match analysis — proceeding to resume build.")
        return True, []

    pct        = match.get("match_pct", 0)
    rating     = match.get("rating", "")
    rec        = match.get("recommendation", "")
    summary    = match.get("summary", "")
    strengths  = match.get("strengths", [])
    gaps       = match.get("gaps", [])
    missing_kw = match.get("missing_keywords", [])

    rec_emoji = {"Go Ahead": "✅", "Proceed with Caution": "⚠️ ", "Not Recommended": "❌"}.get(rec, "")

    print(f"\n{'='*60}")
    print(f"  MATCH REPORT")
    print(f"{'='*60}")
    print(f"  Match Score    : {pct}%  ({rating})")
    print(f"  Recommendation : {rec_emoji} {rec}")
    print(f"\n  {summary}")

    if strengths:
        print(f"\n  Your Strengths for this Role:")
        for s in strengths:
            print(f"    + {s}")

    if gaps:
        print(f"\n  Gaps:")
        for g in gaps:
            print(f"    - {g}")

    if missing_kw:
        print(f"\n  Missing Keywords ({len(missing_kw)}):")
        print(f"    {',  '.join(missing_kw[:20])}" + ("  ..." if len(missing_kw) > 20 else ""))

    print(f"\n{'─'*60}")
    print(f"  Proceed and build a tailored resume targeting 85+ ATS? (yes / no)")
    answer = input("  > ").strip().lower()
    return answer in ("yes", "y"), missing_kw


def main():
    print_banner()
    check_env()

    # Load docs
    print("\n[0/4] Loading your documents from ./docs/ ...")
    resume_docs = load_docs_from_folder("docs")
    if not resume_docs:
        print("  ⚠️  No documents found in ./docs/")
        print("  Add your resume (.pdf, .docx, .txt) to docs/ for best results.")
        print("  Continuing — resume will be a template based on the JD.\n")

    # Get job URL
    job_url = step_get_url()

    # Fetch JD
    job_description = step_fetch_jd(job_url)

    # Smart match analysis
    proceed, missing_keywords = step_show_match(job_description, resume_docs)
    if not proceed:
        print("\n  Exiting. Good luck with your search!\n")
        sys.exit(0)

    # Wait for TPM window to reset between the two GPT calls
    import time
    print("\n  Waiting 65 seconds for API rate limit to reset...")
    time.sleep(65)

    # Build resume
    print("\n[4/4] Building tailored resume targeting 85+ ATS (15-30 seconds)...")
    try:
        result = build_resume(job_description, resume_docs, missing_keywords)
    except (ValueError, RuntimeError) as e:
        print(f"\n  [error] {e}\n")
        sys.exit(1)

    # Show ATS estimate and suggestions
    ats_estimate = result.get("ats_score_estimate", "N/A")
    print(f"\n  Estimated ATS Score : {ats_estimate}/100")

    suggestions = result.get("suggestions", [])
    if suggestions:
        print(f"\n  Tips to push your score higher:")
        for i, s in enumerate(suggestions, 1):
            print(f"    {i}. {s}")

    # Generate Word doc
    tailored = result.get("tailored_resume", {})
    if not tailored:
        print("  [error] No resume data returned. Try again.")
        sys.exit(1)

    try:
        filepath = generate_word_resume(tailored, output_path="output")
        abs_path = os.path.abspath(filepath)
        print(f"\n{'='*60}")
        print(f"  ✅ Resume saved!")
        print(f"  📄 {abs_path}")
        print(f"{'='*60}")
        print("\n  Open the file above to review and download your resume.\n")
    except Exception as e:
        print(f"  [error] Failed to generate Word doc: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
