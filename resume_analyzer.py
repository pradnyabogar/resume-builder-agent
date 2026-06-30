import os
import json
import docx2txt
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SKIP_DIRS = {"archive", "archived", "old", "backup"}
MAX_CHARS_PER_FILE = 20_000   # ~5k tokens per file - increased to capture detailed docs
MAX_CHARS_TOTAL    = 100_000  # ~25k tokens for all docs - increased budget for comprehensive content


def load_docs_from_folder(folder: str = "docs") -> str:
    """
    Recursively read all resume/doc files from docs/ and subfolders.
    Skips: hidden files, archive/old/backup folders, empty files, John Doe placeholders.
    Loads detailed accomplishment and work record docs first to maximize context for latest roles.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"  [warn] Created missing folder: {folder}/")
        return ""

    # Priority folders load first — most recent experience should be listed here
    # Case-insensitive matching to catch "Resume 2026" and "resume 2026"
    PRIORITY_DIRS = ["resume 2026", "resume2026", "2026", "current", "latest"]
    
    # Priority files at root level — load these detailed docs FIRST
    PRIORITY_ROOT_FILES = [
        "pradnya_bogar_accomplishments.docx",      # Most detailed - has Amazon team split
        "pradnya_bogar_complete_work_record.docx", # Detailed work history
        "personal_ai_projects",                     # Personal AI projects
        "pradnyabogar_2026_apr.docx",
        "pradnyabogar_tpm_a"  # prefix match for latest TPM resume
    ]

    combined  = []
    total_chars = 0
    budget_hit  = False

    def _walk_folder(root_path: str):
        nonlocal total_chars, budget_hit
        if budget_hit:
            return
        try:
            entries = os.listdir(root_path)
        except PermissionError:
            return

        dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(root_path, e))
                        and not e.startswith(".") and e.lower() not in SKIP_DIRS])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(root_path, e))])

        # If we're in the root docs folder, sort priority files first
        if root_path == folder:
            def file_priority(fname):
                fname_lower = fname.lower()
                for i, priority_file in enumerate(PRIORITY_ROOT_FILES):
                    if priority_file in fname_lower:
                        return i  # Lower number = higher priority
                return 999  # Non-priority files
            files = sorted(files, key=file_priority)

        # Process files in this directory first
        for fname in files:
            if budget_hit:
                return
            if fname.startswith("."):
                continue
            fpath    = os.path.join(root_path, fname)
            rel_path = os.path.relpath(fpath, folder)
            text     = ""
            try:
                if fname.lower().endswith(".pdf"):
                    with open(fpath, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join(p.extract_text() or "" for p in reader.pages)
                elif fname.lower().endswith((".docx", ".doc")):
                    text = docx2txt.process(fpath)
                elif fname.lower().endswith(".txt"):
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                else:
                    print(f"  [skip] {rel_path} -- unsupported format")
                    continue
            except Exception as e:
                print(f"  [warn] Could not read {rel_path}: {e}")
                continue

            if not text.strip():
                print(f"  [skip] {rel_path} -- empty (PDF may be image-based/scanned)")
                continue
            if "john doe" in text.lower():
                print(f"  [skip] {rel_path} -- placeholder doc")
                continue

            orig_len = len(text)
            if orig_len > MAX_CHARS_PER_FILE:
                text = text[:MAX_CHARS_PER_FILE] + "\n[... trimmed ...]"
                print(f"  [trim] {rel_path} -- {orig_len} -> {MAX_CHARS_PER_FILE} chars")

            if total_chars + len(text) > MAX_CHARS_TOTAL:
                print(f"  [stop] Budget reached at {rel_path}. Move unused files to docs/archive/")
                budget_hit = True
                return

            print(f"  + {rel_path} ({len(text)} chars)")
            combined.append(f"=== {rel_path} ===\n{text.strip()}")
            total_chars += len(text)

        # Then recurse into subdirs — priority dirs go first (case-insensitive)
        priority = [d for d in dirs if d.lower().replace(" ", "") in [p.replace(" ", "") for p in PRIORITY_DIRS]]
        rest     = [d for d in dirs if d.lower().replace(" ", "") not in [p.replace(" ", "") for p in PRIORITY_DIRS]]
        for d in priority + rest:
            _walk_folder(os.path.join(root_path, d))

    _walk_folder(folder)

    print(f"\n  Total: {total_chars} chars from {len(combined)} file(s)")
    if not combined:
        print(f"  [warn] No content loaded from {folder}/")
    return "\n\n".join(combined)


def _parse_json(raw: str) -> dict:
    """Robustly extract JSON from a GPT response, stripping any markdown fences."""
    if not raw:
        raise RuntimeError("GPT returned empty content. Try again.")

    text = raw.strip()

    # Detect refusal
    refusal_phrases = ["i'm sorry", "i cannot", "i can't", "i am unable", "as an ai"]
    if any(p in text.lower()[:100] for p in refusal_phrases):
        raise RuntimeError(
            "GPT refused the request. This usually means something in your docs or the job description "
            "triggered a content filter.\n"
            "Check debug_prompt.txt to see exactly what was sent.\n"
            "Common causes: unusual formatting, special characters, or sensitive-looking text in your docs."
        )

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse GPT response as JSON: {e}\nPreview: {text[:400]}")


def compute_match(job_description: str, resume_docs: str) -> dict:
    """
    Use GPT to semantically compare the candidate's docs against the JD.
    Understands synonyms, related skills, and context — not just keyword counting.
    Returns match percentage, strengths, gaps, and missing keywords.
    """
    system_prompt = """You are a professional resume writer helping a job seeker tailor their resume.
Given a job description and the candidate's existing resume/documents, your task is to:
- Assess how well the candidate's background matches the role
- Identify strengths and gaps
- List important keywords from the JD that are missing from the candidate's docs

Respond with valid JSON only — no markdown fences, no explanation, just the JSON object."""

    user_prompt = f"""JOB DESCRIPTION:
{job_description}

CANDIDATE DOCUMENTS:
{resume_docs or "(none provided)"}

Analyse how well this candidate matches the job. Consider:
- Relevant experience and seniority level
- Skills overlap (including synonyms and related tools, e.g. "GCP" covers "cloud", "Pandas" covers "data manipulation")
- Industry and domain knowledge
- Transferable skills

Return this JSON:
{{
  "match_pct": <0-100, honest percentage of how well the candidate fits this role>,
  "rating": "<one of: Strong Match | Good Match | Partial Match | Weak Match>",
  "recommendation": "<one of: Go Ahead | Proceed with Caution | Not Recommended>",
  "summary": "<2-3 sentences explaining the match honestly>",
  "strengths": ["<specific strength relevant to this JD>"],
  "gaps": ["<specific gap or missing requirement>"],
  "missing_keywords": ["<important JD keywords/skills not reflected in candidate docs>"]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
    except Exception as e:
        raise RuntimeError(f"Match analysis failed: {e}")

    raw = response.choices[0].message.content
    return _parse_json(raw)


def build_resume(job_description: str, resume_docs: str, missing_keywords: list = None) -> dict:
    """Use GPT to build a tailored resume targeting 85+ ATS score."""

    if not job_description or len(job_description.strip()) < 100:
        raise ValueError(
            "Job description is too short or empty. "
            "The site may have blocked scraping -- try pasting the JD manually."
        )

    if len(job_description) > 10_000:
        job_description = job_description[:10_000] + "\n[... trimmed ...]"
    if len(resume_docs) > MAX_CHARS_TOTAL:
        resume_docs = resume_docs[:MAX_CHARS_TOTAL] + "\n[... trimmed ...]"

    missing_kw_section = ""
    if missing_keywords:
        missing_kw_section = (
            "\nKEYWORDS TO WEAVE IN (only where genuinely applicable to the candidate's real experience):\n"
            + ", ".join(missing_keywords[:30])
        )

    no_docs_note = (
        "\nNOTE: No candidate documents provided. Use placeholder values for "
        "personal details and build a template based on the job requirements."
        if not resume_docs.strip() else ""
    )

    system_prompt = """You are a professional resume writer helping a job seeker tailor their resume to a specific job.

YOUR STRICT RULES:

COPY VERBATIM — do not change, invent, or omit:
- Candidate full name, email, phone, LinkedIn (do NOT include physical address or location)
- Every degree, school name, and graduation year
- Every job title, company name, and employment dates
- Every certification
- IMPORTANT: If the candidate held MULTIPLE ROLES/POSITIONS at the same company (different teams, promotions, role changes), create SEPARATE experience entries for each role at that company. Look for indicators like "promoted to", "transitioned to", "moved to [team name]", different job titles with overlapping company employment periods.

REPHRASE ONLY THE WORDING — never the underlying facts:
- Experience bullet points: same facts, stronger action verbs, mirror JD language
  * CRITICAL: Extract 5-7 bullets per role (6-8 bullets for the MOST RECENT role at the top)
  * Go DEEP into the documents — read ALL details about each role across ALL files
  * Each bullet should showcase a major accomplishment, technical delivery, business impact, or leadership responsibility
  * For the LATEST/CURRENT role: prioritize high-impact achievements with quantifiable results (revenue, efficiency, scale)
  * Use strong action verbs (Led, Delivered, Drove, Built, Launched, Scaled, etc.)
  * Weave in JD keywords naturally where they match the candidate's real work
- Professional summary: based only on candidate's real background, 4-5 sentences highlighting most relevant experience for THIS role
- Skills: ONLY include skills from docs that are HIGHLY RELEVANT to this specific JD. Limit to 16-20 most important skills. Exclude outdated or tangential technologies. Focus on: languages/tools mentioned in JD, transferable technical skills, key platforms/methodologies relevant to the role. Skip skills like old programming languages, obsolete tools, or anything not applicable to this job. IMPORTANT: Order skills by JD relevance - most critical skills FIRST (these appear on line 1 of resume), then supporting skills.

NEVER:
- Invent degrees, schools, years, job titles, companies, or dates not in the docs
- Add skills or achievements the candidate has not demonstrated
- Fabricate metrics or numbers not in the docs
- Exclude ANY work experience from 2015 onwards (include ALL jobs from 2015 forward: Qualitrol 2015-2019, Fluke 2019-2021, Helpful Engineering 2021-2022, Amazon 2022-Present)
- Include ANY work experience, jobs, or projects dated 2014 or earlier (education and certifications from any year are fine)
- Include the projects "Nano Internet" or "Mobile Center" — these are outdated and must be excluded
- Mix responsibilities from different roles at the same company into a single entry — keep them separate if candidate had multiple positions

PROJECTS SECTION:
- ONLY include AI/ML-related personal projects (personal AI projects, machine learning experiments, AI tools, LLM/GenAI projects)
- Extract from "Personal AI Projects Summary" document
- DO NOT include: non-AI projects, work-related projects (those belong in experience bullets), old academic projects, COVID ventilator project
- If no AI projects exist in docs, leave projects array empty
- Focus on: AI agents, chatbots, ML models, automation with AI, generative AI applications, prompt engineering projects

EXTRACTION PRIORITY:
1. LATEST ROLE (most recent job): Extract MAXIMUM detail — 6-8 impactful bullets covering major programs, technical scope, business outcomes, stakeholder management, and leadership
2. Previous roles: 5-6 bullets each focusing on most relevant achievements for this JD
3. Older roles (5+ years ago but 2015 or later): 4-5 bullets, focus on transferable skills and major deliverables
4. MULTIPLE ROLES AT SAME COMPANY: If candidate worked in different teams/roles at the same company (e.g., "TPM on Team A" then "TPM on Team B", or "promoted from Engineer to Manager"), create separate experience entries for each role. Check docs for: role changes, team transitions, promotions, different focus areas at the same employer.
5. CRITICAL: Include ALL work experience from 2015 onwards. The candidate's full career timeline is: Qualitrol (2015-2019) → Fluke (2019-2021) → Helpful Engineering (2021-2022) → Amazon (2022-Present with 2 teams). Do NOT skip any of these roles.

READ THOROUGHLY: The candidate documents may contain multiple files describing the same roles — extract ALL relevant details from every file to build comprehensive, achievement-focused bullet points.

Respond with valid JSON only — no markdown fences, no explanation."""

    user_prompt = f"""JOB DESCRIPTION:
{job_description}

CANDIDATE DOCUMENTS (sole source of truth — extract all real data from here):
{resume_docs or "(none provided)"}
{missing_kw_section}
{no_docs_note}

IMPORTANT EXTRACTION INSTRUCTIONS:
- Read through ALL the candidate documents carefully — they contain detailed descriptions of the same roles across multiple files
- For the MOST RECENT/CURRENT role (usually at Amazon): Check if the candidate worked on MULTIPLE TEAMS within the same company
  * Look for mentions of: "Enterprise Engineering", "RME", "Reliability Maintenance Engineering", "Operations", team transitions, different focus areas
  * If found, create SEPARATE experience entries for each team/role at Amazon with different dates
  * Example: "TPM - Enterprise Engineering (dates)" and "TPM - RME (dates)" as separate entries
  * Extract 6-8 bullets per Amazon role (one for Enterprise Engineering work, one for RME work)
- For other roles: extract 5-6 bullets each, focusing on achievements most relevant to THIS job description
- Look for: program scope, team size, budget/revenue impact, technical platforms, stakeholder groups, delivery timelines, process improvements, awards/recognition
- Each bullet should tell a complete story: what was delivered, the technical/business scope, and the measurable impact
- For PROJECTS: ONLY extract AI/ML-related personal projects from "Personal AI Projects Summary" document - NOT work projects, NOT non-AI projects like COVID ventilator (those go in experience bullets)

Return this JSON:
{{
  "ats_score_estimate": <estimated ATS score 0-100>,
  "suggestions": ["<one specific actionable tip to improve the resume further>"],
  "tailored_resume": {{
    "name": "<COPY exact full name from docs>",
    "contact": {{
      "email":    "<COPY exact email from docs>",
      "phone":    "<COPY exact phone from docs>",
      "linkedin": "<COPY exact LinkedIn from docs, or empty string>"
    }},
    "summary": "<3-4 sentences from candidate perspective, real background, tailored to JD>",
    "skills": ["<ONLY include 16-20 most JD-relevant skills from docs — exclude outdated/irrelevant skills. Order by JD relevance: MOST CRITICAL FIRST (tools/platforms mentioned in JD), then supporting skills. Focus on skills directly applicable to this role>"],
    "experience": [
      {{
        "title":   "<CRITICAL: For Amazon, check if candidate worked on different teams. If YES, create 2 separate entries: 'Technical Program Manager - Enterprise Engineering' and 'Technical Program Manager - Reliability Maintenance Engineering'. For other companies, use COPY exact job title from docs>",
        "company": "<COPY exact company name from docs>",
        "dates":   "<CRITICAL: For Amazon with 2 teams, split the date range. Example: if Amazon total is Apr 2022-Present, and they switched teams in mid-2023, do 'Jul 2023-Present' for current team and 'Apr 2022-Jul 2023' for previous team. For other companies, COPY exact dates from docs>",
        "bullets": ["<For Amazon roles: 6-8 bullets EACH (one set for Enterprise Engineering work, one set for RME work). For other roles: 5-6 bullets. Extract comprehensive detail from ALL docs, rephrase with strong action verbs and JD keywords, quantify impact where possible>"]
      }}
    ],
    "education": [
      {{
        "degree": "<COPY exact degree from docs>",
        "school": "<COPY exact school name from docs>",
        "year":   "<COPY exact graduation year from docs>"
      }}
    ],
    "certifications": ["<COPY exact certifications from docs — empty list if none>"],
    "projects": [
      {{
        "name":        "<ONLY AI/ML-related personal projects from 'Personal AI Projects Summary' doc - examples: resume builder AI agent, personal chatbots, ML experiments, AI automation tools. NOT work projects, NOT COVID ventilator>",
        "description": "<real description rephrased with JD keywords, emphasizing AI/ML technologies used>"
      }}
    ]
  }}
}}"""

    # Save debug prompt so you can inspect what GPT receives if it refuses
    with open("debug_prompt.txt", "w", encoding="utf-8") as f:
        f.write("=== SYSTEM PROMPT ===\n" + system_prompt + "\n\n")
        f.write("=== USER PROMPT ===\n" + user_prompt)

    print(f"  Sending to GPT-4o:")
    print(f"    Job description : {len(job_description)} chars")
    print(f"    Candidate docs  : {len(resume_docs)} chars")
    print(f"    Debug prompt    : debug_prompt.txt")
    if resume_docs.strip():
        print(f"    Docs preview    : {resume_docs[:200].replace(chr(10), ' ')}...")
    else:
        print(f"    [warn] No candidate docs — resume will be generic template")
    print()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8000,
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}")

    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(
            "GPT response was cut off (max tokens reached). "
            "Move some files to docs/archive/ to reduce input size and try again."
        )

    return _parse_json(choice.message.content)
