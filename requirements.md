# Job Application Agent — Requirements Document

## 1. Overview

A command-line AI agent that reads a candidate's resume and supporting documents, compares them against a job posting, and generates a tailored Word resume optimised for ATS systems.

---

## 2. Agent Flow

The agent runs in the following sequence:

| Step | Description |
|------|-------------|
| 0 | Load all candidate documents from the `docs/` folder |
| 1 | Ask the user for a job posting URL |
| 2 | Fetch the job description from the URL |
| 3 | Run a smart semantic comparison and show match % |
| 4 | User decides whether to proceed |
| 5 | Build a tailored Word resume targeting 85+ ATS score |
| 6 | Save the resume to `./output/` and prompt the user to download |

---

## 3. Document Loading

### 3.1 Source Folder
- All candidate documents are read from the `docs/` folder
- The folder may contain nested subfolders (e.g. `docs/cover_letters/`, `docs/Resume 2026/`)
- All subfolders are read recursively

### 3.2 Priority Loading
- Folders named `Resume 2026`, `2026`, `current`, or `latest` are loaded first
- This ensures the most recent experience is prioritised when the token budget is reached

### 3.3 Skipped Folders
- Folders named `archive/`, `archived/`, `old/`, or `backup/` are skipped automatically

### 3.4 Supported File Formats
- `.pdf`, `.docx`, `.doc`, `.txt`

### 3.5 Exclusions
- Files with empty content after extraction are skipped
- Files containing "John Doe" are skipped (placeholder documents)
- Image-based / scanned PDFs will be skipped with a warning

### 3.6 Token Budget
- Per-file cap: 15,000 characters
- Total cap: 80,000 characters
- If the budget is reached, remaining files are skipped with a message

---

## 4. Job Description Fetching

### 4.1 URL Scraping
- The agent fetches the job description from the provided URL
- JavaScript-rendered sites (Microsoft, LinkedIn, Workday, Greenhouse, etc.) are detected upfront and skipped — the user is prompted to paste the text manually

### 4.2 Manual Paste Fallback
- If the URL returns less than 100 characters of usable text, the agent drops into manual paste mode
- The user pastes the job description and types `END` on a new line to submit

---

## 5. Match Analysis (Smart Comparison)

- Uses GPT-4o to semantically compare the candidate's documents against the job description
- Considers synonyms, related technologies, transferable skills, and context — not just keyword counting
- Outputs:
  - Match percentage (0–100%)
  - Rating: Strong Match / Good Match / Partial Match / Weak Match
  - Recommendation: Go Ahead / Proceed with Caution / Not Recommended
  - Summary (2–3 sentences)
  - Candidate strengths relevant to the role
  - Gaps and missing requirements
  - Missing keywords from the JD
- User must confirm (yes/no) before the resume is built

---

## 6. Resume Generation

### 6.1 Content Rules

| Section | Rule |
|---------|------|
| Name | Copy verbatim from docs |
| Contact (email, phone, LinkedIn, location) | Copy verbatim from docs |
| Education | Copy verbatim from docs — all entries regardless of date |
| Certifications | Copy verbatim from docs — no additions |
| Work Experience | Copy job titles, company names, and dates verbatim. Rephrase bullet points only (stronger verbs, JD keywords) — same facts, better wording |
| Skills | Copy from docs, reorder by JD relevance — do NOT add new skills |
| Projects | Copy from docs, rephrase description with JD keywords — same facts |
| Summary | Written fresh in first person, based only on candidate's real background, 4–5 sentences |

### 6.2 Date Filters
- Work experience and projects dated before 2015 are excluded
- Education and certifications are kept regardless of date
- Projects "Nano Internet" and "Mobile Center" are explicitly excluded

### 6.3 Bullet Points
- 4–6 bullets per role
- Extract as much relevant detail as possible from the docs
- Rephrase with strong action verbs and JD keywords
- Do not fabricate metrics or achievements not present in the docs

### 6.4 ATS Target
- The resume is optimised to achieve an ATS score of 85 or above
- Missing keywords from the match analysis are woven in naturally where they genuinely reflect the candidate's background
- The agent displays an estimated ATS score after generation

---

## 7. Word Document Formatting

### 7.1 Page Layout
- Narrow margins: 0.5" top/bottom, 0.6" left/right
- Font: Calibri throughout

### 7.2 Typography
- Name: 18pt bold, dark blue
- Section headings: 10pt bold, mid blue, with underline rule
- Body text: 10pt
- Contact line: 8.5pt grey, centred
- Dates: 9pt italic grey, right-aligned via tab stop

### 7.3 Sections
- Skills: borderless 3-column table
- Certifications: borderless 2-column bullet table
- Experience bullets: tight indent, 0–1pt spacing

### 7.4 Output
- Saved to `./output/<CandidateName>_Resume.docx`

---

## 8. API & Rate Limits

- Model: GPT-4o
- API key stored in `.env` as `OPENAI_API_KEY`
- Two GPT calls per run: one for match analysis, one for resume build
- A 65-second wait is inserted between the two calls to avoid hitting the 30,000 TPM rate limit on free/tier-1 accounts

---

## 9. Error Handling

| Error | Behaviour |
|-------|-----------|
| URL cannot be scraped | Falls back to manual paste mode |
| JS-rendered site detected | Skips scraping, prompts paste immediately |
| GPT refuses request | Clear error message, points to `debug_prompt.txt` |
| Token limit (429) | 65-second wait between calls prevents this |
| Response cut off (length) | Error message advising user to move files to `docs/archive/` |
| Empty PDF (scanned) | Skipped with warning |
