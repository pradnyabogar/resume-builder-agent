# Low Level Design (LLD) Document
# Resume Builder Agent

**Version**: 2.0  
**Author**: AI Assistant  
**Date**: June 2026  
**System Type**: Document Processing & AI-Powered Resume Generation

---

## 1. SYSTEM OVERVIEW

### 1.1 Purpose
The Resume Builder Agent is an AI-powered system that analyzes job descriptions, compares them against candidate documents, and generates ATS-optimized, tailored resumes in Word format.

### 1.2 Architecture Pattern
- **Pattern**: Multi-tier Architecture with AI Integration
- **Tiers**:
  1. Presentation Layer (Web UI / CLI)
  2. Application Layer (Flask / Python CLI)
  3. Business Logic Layer (Resume Analysis, Document Processing)
  4. AI Integration Layer (OpenAI GPT-4o)
  5. Data Layer (File System, Document Storage)

### 1.3 Technology Stack
- **Language**: Python 3.8+
- **Web Framework**: Flask 2.x
- **AI/ML**: OpenAI GPT-4o API
- **Document Processing**: docx2txt, PyPDF2, python-docx
- **Web Scraping**: requests, BeautifulSoup4
- **Configuration**: python-dotenv
- **Frontend**: Vanilla JavaScript, CSS3, HTML5

---

## 2. SYSTEM COMPONENTS

### 2.1 Component Diagram
```
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   CLI App    │  │  Web UI v1   │  │  Web UI v2   │ │
│  │  (agent.py)  │  │   (app.py)   │  │(app_option2) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────┐
│         │      APPLICATION LAYER              │         │
│         └─────────────┬────────────────────────┘         │
│                       │                                  │
│         ┌─────────────▼─────────────┐                   │
│         │   Orchestration Logic     │                   │
│         │  (Main workflow control)  │                   │
│         └─────────────┬─────────────┘                   │
└───────────────────────┼──────────────────────────────────┘
                        │
┌───────────────────────┼──────────────────────────────────┐
│         BUSINESS LOGIC LAYER            │                │
│  ┌──────▼───────────┐  ┌───────────────▼─────────┐     │
│  │ resume_analyzer  │  │   doc_generator.py      │     │
│  │      .py         │  │ (Word doc creation)     │     │
│  │                  │  └─────────────────────────┘     │
│  │ - load_docs      │  ┌─────────────────────────┐     │
│  │ - compute_match  │  │   web_reader.py         │     │
│  │ - build_resume   │  │ (Job desc fetching)     │     │
│  └──────────────────┘  └─────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼──────────────────────────────────┐
│         AI INTEGRATION LAYER            │                │
│         ┌─────────────▼─────────────┐                   │
│         │   OpenAI GPT-4o Client    │                   │
│         │  (Match + Resume Build)   │                   │
│         └───────────────────────────┘                   │
└──────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼──────────────────────────────────┐
│         DATA LAYER                      │                │
│  ┌──────────────────┐  ┌───────────────▼─────────┐     │
│  │   docs/          │  │      output/            │     │
│  │ (Input docs)     │  │  (Generated resumes)    │     │
│  └──────────────────┘  └─────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

---

## 3. DETAILED MODULE DESIGN

### 3.1 resume_analyzer.py

#### 3.1.1 Module Purpose
Core business logic for document loading, match analysis, and resume generation.

#### 3.1.2 Key Functions

**Function: load_docs_from_folder(folder: str = "docs") -> str**
- **Purpose**: Recursively load all resume documents from folder
- **Algorithm**:
  ```python
  1. Define skip directories (archive, archived, old, backup)
  2. Define priority folders (resume 2026, 2026, current, latest)
  3. Define priority files (accomplishments, work_record, AI projects)
  4. Walk folder tree:
     a. Process priority files first
     b. Read .docx, .pdf, .txt files
     c. Skip John Doe placeholders
     d. Trim files > 20k chars
     e. Stop if total > 100k chars
  5. Return concatenated text
  ```
- **Input**: Folder path (default: "docs")
- **Output**: String containing all document text
- **Constraints**:
  - MAX_CHARS_PER_FILE = 20,000 (~5k tokens)
  - MAX_CHARS_TOTAL = 100,000 (~25k tokens)
- **Error Handling**: Skips unreadable files, logs warnings

**Function: compute_match(job_description: str, resume_docs: str) -> dict**
- **Purpose**: Semantic comparison of candidate vs job requirements
- **Algorithm**:
  ```python
  1. Build system prompt (professional resume writer persona)
  2. Build user prompt with JD and resume docs
  3. Call OpenAI GPT-4o:
     - Model: gpt-4o
     - Temperature: 0.2 (deterministic)
     - Max tokens: 1000
  4. Parse JSON response
  5. Return match analysis
  ```
- **Input**: 
  - job_description: string (job posting text)
  - resume_docs: string (candidate documents)
- **Output**: dict with keys:
  ```python
  {
    "match_pct": int (0-100),
    "rating": str ("Strong Match" | "Good Match" | "Partial Match" | "Weak Match"),
    "recommendation": str ("Go Ahead" | "Proceed with Caution" | "Not Recommended"),
    "summary": str (2-3 sentences),
    "strengths": list[str],
    "gaps": list[str],
    "missing_keywords": list[str]
  }
  ```
- **AI Prompt Strategy**: 
  - Semantic understanding (considers synonyms, related skills)
  - Context-aware (industry knowledge, transferable skills)
  - Honest assessment (no false positives)

**Function: build_resume(job_description: str, resume_docs: str, missing_keywords: list) -> dict**
- **Purpose**: Generate tailored resume JSON structure
- **Algorithm**:
  ```python
  1. Validate inputs (JD length > 100 chars)
  2. Trim if needed (JD < 10k, docs < 100k)
  3. Build comprehensive system prompt with rules:
     - Copy verbatim: name, contact, dates, titles, companies
     - Rephrase: bullet points, summary
     - Filter: skills by relevance
     - Extract: 6-8 bullets for latest, 5-6 for others
     - Split: multiple roles at same company
     - Projects: AI-related personal projects only
  4. Build user prompt with detailed extraction instructions
  5. Save debug prompt to file
  6. Call OpenAI GPT-4o:
     - Model: gpt-4o
     - Temperature: 0.1 (very deterministic)
     - Max tokens: 8000
  7. Parse JSON response
  8. Return resume data structure
  ```

- **Output**: dict with resume data structure
- **Critical Rules Enforced**:
  1. No fabrication of facts
  2. Include ALL roles from 2015 onwards
  3. Exclude roles from 2014 or earlier
  4. Split Amazon into Enterprise Engineering & RME roles
  5. Only AI projects in Projects section
  6. 16-20 most relevant skills, prioritized
  7. No physical location in contact
  8. Remove old projects: Nano Internet, Mobile Center

#### 3.1.3 Data Structures

**Resume Data Structure (Output of build_resume)**
```python
{
  "ats_score_estimate": int,
  "suggestions": list[str],
  "tailored_resume": {
    "name": str,
    "contact": {
      "email": str,
      "phone": str,
      "linkedin": str
    },
    "summary": str,
    "skills": list[str],  # 16-20 items, prioritized
    "experience": [
      {
        "title": str,
        "company": str,
        "dates": str,
        "bullets": list[str]  # 6-8 for latest, 5-6 for others
      }
    ],
    "education": [
      {
        "degree": str,
        "school": str,
        "year": str
      }
    ],
    "certifications": list[str],
    "projects": [  # AI projects only
      {
        "name": str,
        "description": str
      }
    ]
  }
}
```

---

### 3.2 doc_generator.py

#### 3.2.1 Module Purpose
Generate formatted Word (.docx) documents from resume data structure.

#### 3.2.2 Key Functions

**Function: generate_word_resume(resume_data: dict, output_path: str) -> str**
- **Purpose**: Create professionally formatted Word resume
- **Algorithm**:
  ```python
  1. Create new Document()
  2. Set page margins (0.5" top/bottom, 0.6" left/right)
  3. Add sections in order:
     a. Name (18pt, centered, blue)
     b. Contact line (8.5pt, centered, pipe-separated)
     c. Professional Summary (10pt, justified)
     d. Core Skills (2 lines, bullet-separated)
     e. Professional Experience (with bullets)
     f. Education
     g. Certifications (2-column table)
     h. Projects (AI projects only)
  4. Apply formatting and spacing
  5. Generate timestamped filename
  6. Save to output folder
  7. Return filepath
  ```
- **Input**: resume_data dict, output_path string
- **Output**: String (full path to generated .docx file)

#### 3.2.3 Formatting Specifications

**Color Palette**
```python
BLUE_DARK  = RGBColor(31,  73,  125)   # Name
BLUE_MID   = RGBColor(68,  114, 196)   # Section headings
GREY_MED   = RGBColor(89,  89,  89)    # Company, school
GREY_LIGHT = RGBColor(127, 127, 127)   # Dates
BLACK      = RGBColor(0,   0,   0)     # Body text
```

**Typography**
- Font: Calibri (all content)
- Name: 18pt bold
- Section Headings: 10pt bold
- Contact: 8.5pt
- Body text: 10pt
- Dates: 9pt italic

**Spacing**
- Section heading before: 6pt
- Section heading after: 1pt
- Experience title before: 5pt
- Experience title after: 1pt
- Bullet points: 0pt before, 1pt after
- Paragraph line spacing: Default (1.15)

**Skills Section Layout**
- Format: 2 lines, bullet-separated
- Split: First line gets ceiling(count/2) skills
- Separator: " • " between skills

**Experience Bullets**
- Alignment: Justified
- Indent: 0.15" left, -0.15" first line (hanging)
- Style: List bullet

**Filename Convention**
```python
Format: {name}_{MMDDYYYY}_{HHMM}.docx
Example: Pradnya_Bogar_06302026_1430.docx
```

---

### 3.3 web_reader.py

#### 3.3.1 Module Purpose
Fetch job descriptions from URLs with fallback to manual paste.

#### 3.3.2 Key Function

**Function: fetch_job_description(url: str) -> tuple[str, str]**
- **Algorithm**:
  ```python
  1. Check if domain requires JavaScript:
     - If yes: return empty text + warning
  2. Send HTTP GET with browser headers
  3. Parse HTML with BeautifulSoup
  4. Remove script, style, nav, footer, header tags
  5. Try job-site-specific selectors:
     - Greenhouse: id="content"
     - Lever: class="content"
     - Workday: data-automation-id="jobPostingDescription"
     - Indeed: id="jobDescriptionText"
     - LinkedIn: class="description__text"
     - Generic: class contains "job-description"
  6. If no match, extract from body tag
  7. Clean whitespace and newlines
  8. Detect if JavaScript config returned
  9. Return (text, warning)
  ```
- **Output**: tuple (text: str, warning: str)
- **JS-Only Domains**: microsoft.com, linkedin.com, workday.com, greenhouse.io, etc.

---

### 3.4 Flask Applications

#### 3.4.1 app.py (Option 1 - Auto)

**Routes**:
1. `GET /` - Serve index.html
2. `POST /upload` - Handle file uploads to docs/
3. `POST /fetch-jd` - Fetch job description from URL
4. `POST /run` - Start background job (match + build)
5. `GET /status/<job_id>` - Poll job progress
6. `GET /download/<filename>` - Download generated resume

**Background Processing**:
```python
def run_agent(job_id, job_description):
  1. Load docs
  2. Compute match
  3. Wait 65 seconds (rate limit)
  4. Build resume
  5. Generate Word doc
  6. Update job status to "done"
```

**State Management**:
- In-memory dict: `jobs = {job_id: {status, message, match, filename, ...}}`
- Thread-safe: Each job runs in separate daemon thread

#### 3.4.2 app_option2.py (Option 2 - Manual)

**Differences from Option 1**:
1. **Two-step workflow**: Match first, then build
2. **Two endpoints**: `/calculate-ats` and `/build-resume`
3. **Match caching**: Stores match results for reuse
4. **User control**: Shows match, user decides to build or cancel

**Routes**:
1. `GET /` - Serve index_option2.html
2. `POST /upload` - Handle file uploads
3. `POST /fetch-jd` - Fetch job description
4. `POST /calculate-ats` - Run match analysis only
5. `POST /build-resume` - Build resume using cached match
6. `GET /status/<job_id>` - Poll job progress
7. `GET /download/<filename>` - Download resume

**State Management**:
```python
jobs = {job_id: {status, message, match, filename, ...}}
match_cache = {
  job_id: {
    resume_docs: str,
    job_description: str,
    match: dict
  }
}
```

---

## 4. DATA FLOW DIAGRAMS

### 4.1 Option 1 (Auto) - End-to-End Flow

```
User Action                System Process                    AI Call
───────────                ───────────────                   ────────
Upload docs   ────────>    Store in docs/
                              │
Paste JD      ────────>    Validate JD
                              │
Click Generate ────────>   Create job_id
                              │
                           Load all docs ────────>
                              │                   
                           Format prompt  ────────> GPT-4o Match
                              │                     Analysis
                              │<────────────────    (15 sec)
                           Parse match result
                              │
                           Wait 65 seconds
                              │
                           Format prompt  ────────> GPT-4o Resume
                              │                     Build
                              │<────────────────    (20 sec)
                           Parse resume JSON
                              │
                           Generate .docx
                              │
Download      <────────    Save file
                           Return filename
```


### 4.2 Option 2 (Manual) - Two-Step Flow

```
User Action                System Process                    AI Call
───────────                ───────────────                   ────────
Upload docs   ────────>    Store in docs/
                              │
Paste JD      ────────>    Validate JD
                              │
Click Calculate ───────>   Create job_id
                              │
                           Load all docs ────────>
                              │                   
                           Format prompt  ────────> GPT-4o Match
                              │                     Analysis
                              │<────────────────    (15 sec)
                           Parse & cache match
                              │
                           Display results
                              │
[USER DECISION POINT]         │
  ├─ Cancel   ────────>    Stop (no resume)
  │
  └─ Build    ────────>    Retrieve cached data
                              │
                           Wait 65 seconds
                              │
                           Format prompt  ────────> GPT-4o Resume
                              │                     Build
                              │<────────────────    (20 sec)
                           Parse resume JSON
                              │
                           Generate .docx
                              │
Download      <────────    Save file
                           Return filename
```

---

## 5. TOKEN BUDGET & COST ANALYSIS

### 5.1 Token Budget Configuration

**Input Token Budget**
```python
MAX_CHARS_PER_FILE = 20,000 chars   # ~5,000 tokens per file
MAX_CHARS_TOTAL    = 100,000 chars  # ~25,000 tokens total docs
JD_MAX_CHARS       = 10,000 chars   # ~2,500 tokens for job description

Total Input Tokens per Request: ~27,500 tokens
```

**Output Token Allocation**
- Match Analysis: 1,000 tokens max
- Resume Build: 8,000 tokens max

**Rate Limit Constraints**
- OpenAI Free Tier: 30,000 TPM (tokens per minute)
- Strategy: 65-second wait between calls
- Calculation:
  ```
  Call 1 (Match): 27,500 input + 1,000 output = 28,500 tokens
  Wait: 65 seconds (> 60 seconds to reset TPM)
  Call 2 (Resume): 27,500 input + 8,000 output = 35,500 tokens
  
  Total: 64,000 tokens over 2+ minutes = Compliant with 30k TPM
  ```

### 5.2 Cost Analysis (OpenAI GPT-4o Pricing)

**Pricing Structure (as of June 2026)**
- Input tokens: $2.50 per 1M tokens
- Output tokens: $10.00 per 1M tokens

**Per-Request Cost Breakdown**

**Match Analysis Call**
```
Input:  27,500 tokens × $2.50/1M  = $0.069
Output:  1,000 tokens × $10.00/1M = $0.010
Total Match Cost: $0.079 (~$0.08)
```

**Resume Build Call**
```
Input:  27,500 tokens × $2.50/1M  = $0.069
Output:  8,000 tokens × $10.00/1M = $0.080
Total Resume Cost: $0.149 (~$0.15)
```

**Total Cost per Complete Run**
```
Match + Resume = $0.08 + $0.15 = $0.23 per resume
```

**Option 2 Cost Savings**
```
If user cancels after match: Only $0.08 spent
Savings per cancelled job: $0.15 (65% cost reduction)

Example: Apply to 10 jobs, 6 are poor matches
- Option 1: 10 × $0.23 = $2.30
- Option 2: 4 × $0.23 + 6 × $0.08 = $0.92 + $0.48 = $1.40
- Savings: $0.90 (39% reduction)
```

### 5.3 Budget Optimization Strategies

**Document Loading Optimization**
1. **Priority-based loading**: Load most relevant docs first
   - Accomplishments doc: Most detailed, loads first
   - Complete Work Record: Comprehensive, loads second
   - Recent resumes (2026): Most current info
   - Older resumes: Loaded if budget allows

2. **Truncation Strategy**:
   ```python
   Per-file limit: 20k chars (prevents single large file from consuming budget)
   Total limit: 100k chars (ensures room for system prompt + output)
   
   If file > 20k chars: Trim and add "[... trimmed ...]" marker
   If total > 100k chars: Stop loading, suggest moving files to archive/
   ```

3. **Skip Patterns**:
   - Archive/old/backup folders automatically excluded
   - Empty files skipped
   - John Doe placeholders filtered out
   - PDFs that are image-based (no extractable text) skipped

### 5.4 Performance Metrics

**Timing Analysis**
```
Component                    Time          Bottleneck
─────────────────────────    ────          ──────────
Document Loading             2-5 sec       File I/O
Job Description Fetch        3-8 sec       Network
Match Analysis (GPT)         10-20 sec     API call
Rate Limit Wait              65 sec        Hard requirement
Resume Build (GPT)           15-25 sec     API call
Word Doc Generation          1-2 sec       CPU/Memory
────────────────────────────────────────────────────
Option 1 Total:              96-125 sec    (~1.5-2 min)
Option 2 Match Only:         15-33 sec     (~15-30 sec)
Option 2 Full:               96-125 sec    (if user proceeds)
```

**Token Utilization**
```
Component                    Tokens Used   % of 30k TPM
─────────────────────────    ───────────   ────────────
Input (docs + JD)            27,500        91.7%
Match output                  1,000         3.3%
Resume output                 8,000        26.7%
────────────────────────────────────────────────────
Call 1 (Match):              28,500        95.0%
Call 2 (Resume):             35,500       118.3% (needs wait)
```

---

## 6. ALTERNATIVE APPROACHES CONSIDERED

### 6.1 AI Model Selection

**Approach 1: OpenAI GPT-4o (SELECTED)**
- **Pros**:
  - Best quality for complex instructions
  - Excellent semantic understanding
  - Reliable JSON output
  - 128k context window
- **Cons**:
  - Higher cost ($0.23/resume)
  - Rate limits on free tier
- **Why chosen**: Quality and reliability outweigh cost for resume generation

**Approach 2: Claude 3.5 Sonnet (CONSIDERED)**
- **Pros**:
  - Comparable quality
  - Good instruction following
  - 200k context window
- **Cons**:
  - Similar pricing
  - Would require API key change
  - Less familiar with output format
- **Why not chosen**: No significant advantage over GPT-4o

**Approach 3: Open Source LLM (Llama 3, Mistral) (REJECTED)**
- **Pros**:
  - No API costs
  - No rate limits
  - Data privacy
- **Cons**:
  - Requires local GPU or cloud compute
  - Lower quality outputs
  - More prompt engineering needed
  - Hosting costs may exceed API costs
- **Why not chosen**: Quality not sufficient for professional resumes


### 6.2 Document Processing Approaches

**Approach 1: Direct File Reading (SELECTED)**
- **Method**: Read files on-demand, concatenate text
- **Pros**:
  - Simple implementation
  - No database overhead
  - Easy to add/remove documents
- **Cons**:
  - Re-reads files every run
  - No caching between runs
- **Why chosen**: Simplicity, docs change frequently during job search

**Approach 2: Database Storage (CONSIDERED)**
- **Method**: Parse docs once, store in SQLite/PostgreSQL
- **Pros**:
  - Faster subsequent runs
  - Can index and search
  - Version history possible
- **Cons**:
  - Added complexity
  - Schema maintenance
  - Sync issues between files and DB
- **Why not chosen**: Over-engineering for personal use case

**Approach 3: Vector Database (REJECTED)**
- **Method**: Embed docs, use semantic search (Pinecone, Chroma)
- **Pros**:
  - Could fetch only relevant sections
  - Reduce token usage
  - Better for large document sets
- **Cons**:
  - Adds embedding costs
  - Risk of missing relevant content
  - Additional complexity
- **Why not chosen**: Token budget (100k chars) is sufficient

### 6.3 Resume Generation Approaches

**Approach 1: AI-Generated Word Doc (SELECTED)**
- **Method**: GPT generates JSON → python-docx creates .docx
- **Pros**:
  - Full control over formatting
  - Consistent output
  - Easy to modify layout
- **Cons**:
  - Two-stage process
  - Formatting in code
- **Why chosen**: Best quality and control

**Approach 2: AI Direct to Word (REJECTED)**
- **Method**: Prompt GPT to output Word XML/markdown
- **Pros**:
  - Single-stage process
- **Cons**:
  - Unreliable formatting
  - Limited styling control
  - Word XML is complex
- **Why not chosen**: Poor output quality

**Approach 3: Template-based (CONSIDERED)**
- **Method**: Fill pre-made Word template with data
- **Pros**:
  - Very consistent formatting
  - Easy to customize template
- **Cons**:
  - Less flexible for varying content lengths
  - Template maintenance
- **Why not chosen**: Dynamic content needs (variable bullet counts)

### 6.4 UI/UX Approaches

**Approach 1: CLI + Web UI (SELECTED)**
- **Implementations**: 
  - CLI: agent.py, test_quick.py
  - Web Option 1: app.py (auto)
  - Web Option 2: app_option2.py (manual decision)
- **Pros**:
  - Multiple access patterns
  - CLI for power users/testing
  - Web for user-friendly experience
  - Option 2 gives control
- **Cons**:
  - More code to maintain
- **Why chosen**: Flexibility for different use cases

**Approach 2: Web-only (CONSIDERED)**
- **Method**: Only Flask web interface
- **Pros**:
  - Single interface
  - User-friendly
- **Cons**:
  - Harder to test/debug
  - No scripting capability
- **Why not chosen**: CLI useful for development

**Approach 3: Desktop App (REJECTED)**
- **Method**: Electron, PyQt, or Tkinter GUI
- **Pros**:
  - Native experience
  - No server needed
- **Cons**:
  - More complex deployment
  - Platform-specific builds
  - Harder to update
- **Why not chosen**: Web is simpler, browser-based is sufficient

### 6.5 Rate Limit Handling

**Approach 1: Fixed 65-second Wait (SELECTED)**
- **Method**: time.sleep(65) between calls
- **Pros**:
  - Simple, guaranteed to work
  - No complex logic
- **Cons**:
  - Always waits full time even if not needed
  - User waits even if under limit
- **Why chosen**: Reliability over speed for free tier

**Approach 2: Dynamic Wait (CONSIDERED)**
- **Method**: Track token usage, calculate wait needed
- **Pros**:
  - Faster when possible
  - Optimal throughput
- **Cons**:
  - Complex token tracking
  - Clock sync issues
  - Risk of hitting limit
- **Why not chosen**: Not worth complexity for personal use

**Approach 3: Batch Processing (REJECTED)**
- **Method**: Queue multiple jobs, process within TPM limit
- **Pros**:
  - Efficient for multiple resumes
  - Better throughput
- **Cons**:
  - Complex queue management
  - Not needed for single-user
- **Why not chosen**: Over-engineering for use case

---

## 7. SCALABILITY CONSIDERATIONS

### 7.1 Current Limitations

**Single User Design**
- In-memory job storage (not persistent)
- No authentication/authorization
- File system for document storage
- Local Flask server

**Token Budget**
- Free tier: 30k TPM limit
- Max 1 resume per 2 minutes
- Max ~30 resumes per hour (practical limit)

### 7.2 Future Scaling Options

**For Multi-User (Not Implemented)**
1. **Database**: PostgreSQL for job/user data
2. **Auth**: User accounts with JWT tokens
3. **Storage**: S3/cloud storage for documents
4. **Queue**: Redis/Celery for background jobs
5. **Cache**: Redis for match results
6. **Deployment**: Containerized (Docker) on cloud

**For Higher Volume (Not Implemented)**
1. **Paid Tier**: Upgrade to OpenAI paid plan
2. **Batch API**: Use OpenAI Batch API (50% cost reduction)
3. **Caching**: Cache match results for identical JDs
4. **Optimization**: Reduce input tokens with summarization

---

## 8. ERROR HANDLING & EDGE CASES

### 8.1 Error Categories

**1. File Reading Errors**
- **Case**: Corrupted/unreadable file
- **Handling**: Skip file, log warning, continue
- **User Impact**: Minimal, uses other available docs

**2. Rate Limit Errors**
- **Case**: 30k TPM exceeded despite 65s wait
- **Handling**: Catch exception, show clear error message
- **User Action**: Wait additional time, retry
- **Prevention**: 65-second wait is conservative

**3. API Failures**
- **Case**: OpenAI API down/timeout
- **Handling**: RuntimeError with descriptive message
- **User Impact**: Cannot proceed, must retry
- **Mitigation**: None (external dependency)

**4. JSON Parse Errors**
- **Case**: GPT returns invalid JSON
- **Handling**: Try to extract JSON from markdown fences
- **Fallback**: Show error with preview of response
- **Prevention**: Explicit "JSON only" in prompt

**5. Content Filter Triggers**
- **Case**: GPT refuses due to content policy
- **Handling**: Detect refusal phrases, show specific error
- **User Action**: Check debug_prompt.txt, modify problematic content
- **Note**: Rare, usually from unusual formatting in docs


### 8.2 Edge Case Handling

**Empty/Short Job Description**
```python
if len(job_description) < 100:
    raise ValueError("Job description too short")
```

**No Documents Loaded**
```python
if not resume_docs.strip():
    print("[warn] No content loaded from docs/")
    # Continues with warning (GPT will use placeholder)
```

**John Doe Placeholder Detection**
```python
if "john doe" in text.lower():
    print(f"[skip] {filename} -- placeholder doc")
    continue
```

**Budget Overflow**
```python
if total_chars + len(text) > MAX_CHARS_TOTAL:
    print(f"[stop] Budget reached. Move unused files to archive/")
    break
```

**Multiple Roles Detection**
```python
# In GPT prompt:
"If candidate worked in different teams/roles at same company,
create SEPARATE experience entries for each role.
Look for: 'Enterprise Engineering', 'RME', role transitions"
```

---

## 9. SECURITY CONSIDERATIONS

### 9.1 API Key Protection

**Storage**
- Stored in `.env` file (gitignored)
- Not committed to version control
- Environment variable: `OPENAI_API_KEY`

**Access**
- Read via `python-dotenv`
- Not exposed in logs
- Not sent to frontend

### 9.2 File Upload Security (Web UI)

**Validation**
```python
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
```

**Sanitization**
```python
from werkzeug.utils import secure_filename
safe_name = secure_filename(user_filename)
```

**Size Limit**
```python
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
```

### 9.3 Web Scraping Ethics

**Robots.txt Compliance**: Not implemented (would reject many job sites)
**Rate Limiting**: Single request per job URL
**User Agent**: Identifies as browser, not bot
**Fallback**: Manual paste when sites block scraping

**JS-Only Domain Detection**
```python
JS_ONLY_DOMAINS = [
    "microsoft.com", "linkedin.com", "workday.com",
    "greenhouse.io", "lever.co", ...
]
# Returns empty + warning instead of attempting scrape
```

### 9.4 Data Privacy

**User Data**
- Stays local (not sent anywhere except OpenAI)
- No persistent storage in web UI
- In-memory state cleared on server restart

**OpenAI Data**
- Sent to OpenAI API (required for functionality)
- Subject to OpenAI's data usage policy
- Not used for training (API data policy)

---

## 10. DEPLOYMENT & CONFIGURATION

### 10.1 Environment Setup

**Required Python Version**: 3.8+

**Dependencies** (requirements.txt):
```
Flask==2.3.0
openai==1.0.0
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.0
lxml==4.9.0
docx2txt==0.8
PyPDF2==3.0.0
python-docx==0.8.11
```

**Environment Variables** (.env):
```
OPENAI_API_KEY=sk-...
```

### 10.2 Running the Application

**CLI Mode**
```bash
python agent.py
# Interactive: prompts for URL/JD, shows progress, generates resume
```

**Quick Test**
```bash
python test_quick.py
# Automated test with hardcoded Microsoft TPM job
```

**Web UI Option 1 (Auto)**
```bash
python app.py
# Opens on http://localhost:5000
```

**Web UI Option 2 (Manual Decision)**
```bash
python app_option2.py
# Opens on http://localhost:5001
```

### 10.3 File Structure

```
resume-builder-agent/
├── .env                      # API keys (gitignored)
├── .env.example              # Template for .env
├── .gitignore                # Git exclusions
├── requirements.txt          # Python dependencies
├── README.md                 # User documentation
├── LLD_Resume_Builder_Agent.md  # This document
│
├── agent.py                  # CLI application
├── test_quick.py             # Automated test script
├── verify_loading.py         # Doc loading verification
│
├── resume_analyzer.py        # Core business logic
├── doc_generator.py          # Word doc generation
├── web_reader.py             # Job description fetching
├── job_searcher.py           # (unused - job search feature)
│
├── app.py                    # Flask web UI - Option 1
├── app_option2.py            # Flask web UI - Option 2
│
├── templates/
│   ├── index.html            # Web UI - Option 1
│   └── index_option2.html    # Web UI - Option 2
│
├── static/
│   ├── style.css             # Styles - Option 1
│   ├── style_option2.css     # Styles - Option 2
│   ├── app.js                # Frontend JS - Option 1
│   └── app_option2.js        # Frontend JS - Option 2
│
├── docs/                     # Input documents (gitignored)
│   ├── Personal_AI_Projects_Summary.docx
│   ├── Pradnya_Bogar_Accomplishments.docx
│   ├── Pradnya_Bogar_Complete_Work_Record.docx
│   └── [other resume docs]
│
└── output/                   # Generated resumes (gitignored)
    └── Pradnya_Bogar_MMDDYYYY_HHMM.docx
```

---

## 11. TESTING STRATEGY

### 11.1 Unit Testing (Not Implemented)

**Potential Test Cases**:
- Document loading with various file types
- Priority file ordering
- Budget limit enforcement
- JSON parsing with edge cases
- Word document generation
- Filename sanitization

### 11.2 Integration Testing

**Current Approach**: Manual testing via test scripts
- `test_quick.py`: Full workflow with hardcoded job
- `verify_loading.py`: Document loading verification
- `agent.py`: Interactive testing

### 11.3 Quality Assurance

**Resume Quality Checks**:
1. No fabricated information
2. All roles from 2015+ included
3. Amazon split into 2 roles
4. Only AI projects in Projects section
5. 16-20 relevant skills, 2 lines
6. 6-8 bullets for latest role
7. No location in contact
8. Justified text alignment
9. Timestamped filename

**Manual Verification**:
- Check `debug_prompt.txt` for prompt correctness
- Review generated resume in Word
- Verify bullet count per role
- Confirm skills relevance
- Check projects section content

---

## 12. MONITORING & DEBUGGING

### 12.1 Debug Outputs

**debug_prompt.txt**
- Created on every `build_resume()` call
- Contains exact prompt sent to GPT
- Useful for:
  - Verifying document content loaded
  - Checking instruction clarity
  - Debugging GPT refusals

**Console Logging**
```python
# Document loading
"+ filename (X chars)"
"[skip] filename -- reason"
"[trim] filename -- X -> Y chars"
"[stop] Budget reached at filename"

# API calls
"Sending to GPT-4o:"
"  Job description: X chars"
"  Candidate docs: X chars"

# Progress
"[1/4] Loading documents..."
"[2/4] Computing match score..."
"[3/4] Building tailored resume..."
"[4/4] Generating Word document..."
```

### 12.2 Error Messages

**User-Friendly Errors**:
- Rate limit exceeded: "Wait 1-2 minutes and try again"
- GPT refusal: "Check debug_prompt.txt for content issues"
- No docs loaded: "Add .docx/.pdf files to docs/ folder"
- JD too short: "Job description must be at least 50 characters"

---

## 13. FUTURE ENHANCEMENTS (Not Implemented)

### 13.1 Planned Features
1. **Cover Letter Generation**: Auto-generate tailored cover letters
2. **ATS Score Prediction**: More accurate scoring algorithm
3. **Multiple Resume Formats**: PDF, HTML, LinkedIn format
4. **Resume Versioning**: Track different versions for different jobs
5. **Job Tracking**: Dashboard to track applications
6. **A/B Testing**: Multiple resume variants

### 13.2 Technical Improvements
1. **Caching Layer**: Redis for match results
2. **Async Processing**: Better concurrency handling
3. **Progress WebSocket**: Real-time updates without polling
4. **Resume Comparison**: Side-by-side before/after
5. **Skill Gap Analysis**: Detailed gap closure recommendations

---

## APPENDIX A: GPT PROMPT STRUCTURE

### System Prompt (build_resume)
```
Role: Professional resume writer
Rules: Copy verbatim (names, dates, titles)
       Rephrase only (bullets, summary)
       Filter skills by JD relevance
       Split multiple roles per company
       Extract max detail from all docs
Constraints: No fabrication
            Include 2015+ only
            AI projects only
            16-20 skills, prioritized
Output: JSON only, no markdown
```

### User Prompt (build_resume)
```
JOB DESCRIPTION:
[job text]

CANDIDATE DOCUMENTS:
[all docs concatenated]

EXTRACTION INSTRUCTIONS:
- Read ALL files thoroughly
- Check for Amazon team split (EE vs RME)
- 6-8 bullets for latest, 5-6 for others
- AI projects only in Projects section

Return JSON: [structure defined]
```

---

## APPENDIX B: LESSONS LEARNED

### B.1 What Worked Well
1. **Priority loading**: Most important docs load first
2. **65-second wait**: Reliable rate limit compliance
3. **Two-step workflow**: Users appreciate control
4. **Explicit prompts**: Clear rules = better outputs
5. **Debug file**: Essential for troubleshooting

### B.2 Challenges Faced
1. **Rate limits**: Initial 30k TPM exceeded
2. **JSON parsing**: GPT occasionally added markdown
3. **Content filtering**: Rare false positives
4. **Document quality**: Inconsistent source docs
5. **Bullet extraction**: Needed explicit "read ALL files" instruction

### B.3 Key Design Decisions
1. **Python over Node.js**: Better document processing libraries
2. **Flask over Django**: Lightweight, sufficient for needs
3. **GPT-4o over GPT-3.5**: Quality worth the cost
4. **Word over PDF**: Easier to edit after generation
5. **CLI + Web**: Flexibility for different users

---

**END OF LOW LEVEL DESIGN DOCUMENT**

Version: 2.0  
Last Updated: June 2026  
Total Pages: 17
