# Resume Builder Agent - Improvements Made

## Issue Identified
The resume extraction was shallow and not pulling enough detail, especially for your latest Amazon TPM role.

## Root Causes Found

### 1. **Priority Folder Not Loading** (CRITICAL)
- Your detailed resumes are in `docs/RESUME/Resume 2026/`
- Code was looking for `"resume 2026"` (lowercase) but folder is `"Resume 2026"` (capital R)
- **FIX**: Made folder matching case-insensitive and space-insensitive

### 2. **Budget Too Small**
- Only loading ~80k characters (20k tokens) total
- Your new detailed docs (`Pradnya_Bogar_Accomplishments.docx`, `Pradnya_Bogar_Complete_Work_Record.docx`) contain rich detail but weren't being fully loaded
- **FIX**: Increased budget to 100k characters (25k tokens) and per-file to 20k chars

### 3. **File Loading Order Wrong**
- Generic resumes were loading before detailed accomplishment docs
- **FIX**: Added priority file list to load most detailed docs FIRST:
  1. `Pradnya_Bogar_Accomplishments.docx`
  2. `Pradnya_Bogar_Complete_Work_Record.docx`
  3. `PradnyaBogar_2026_apr.docx`
  4. Latest TPM resumes

### 4. **GPT Prompt Not Specific Enough**
- Old prompt said "4-6 bullets per role"
- Didn't emphasize extracting MAXIMUM detail for latest role
- **FIX**: Enhanced prompt to:
  - Extract **6-8 bullets for LATEST/CURRENT role** (Amazon TPM)
  - Extract **5-6 bullets for other roles**
  - Explicitly instruct to "READ THOROUGHLY across ALL files"
  - Added extraction priority instructions
  - Added specific detail to look for: program scope, team size, revenue impact, stakeholder groups, technical platforms, etc.

## Changes Made to `resume_analyzer.py`

### Budget Increases (Lines 11-12)
```python
MAX_CHARS_PER_FILE = 20_000   # ~5k tokens per file - increased to capture detailed docs
MAX_CHARS_TOTAL    = 100_000  # ~25k tokens for all docs - increased budget
```

### Priority File Loading (Lines 30-36)
```python
# Priority files at root level — load these detailed docs FIRST
PRIORITY_ROOT_FILES = [
    "pradnya_bogar_accomplishments.docx",
    "pradnya_bogar_complete_work_record.docx",
    "pradnyabogar_2026_apr.docx",
    "pradnyabogar_tpm_a"  # prefix match for latest TPM resume
]
```

### Case-Insensitive Folder Matching (Lines 117-119)
```python
# Then recurse into subdirs — priority dirs go first (case-insensitive)
priority = [d for d in dirs if d.lower().replace(" ", "") in [p.replace(" ", "") for p in PRIORITY_DIRS]]
rest     = [d for d in dirs if d.lower().replace(" ", "") not in [p.replace(" ", "") for p in PRIORITY_DIRS]]
```

### Enhanced GPT System Prompt (Lines ~230-265)
- Added **EXTRACTION PRIORITY** section
- Specified bullet counts: 6-8 for latest, 5-6 for others, 4-5 for older roles
- Added instruction to "READ THOROUGHLY: The candidate documents may contain multiple files describing the same roles"
- Emphasized extracting comprehensive detail

### Enhanced GPT User Prompt (Lines ~270-285)
- Added **IMPORTANT EXTRACTION INSTRUCTIONS** section
- Explicit guidance on what details to extract: program scope, team size, budget/revenue impact, technical platforms, stakeholder groups, delivery timelines, process improvements, awards
- Emphasized "Each bullet should tell a complete story: what was delivered, the technical/business scope, and the measurable impact"

## What This Will Do

When you run the agent next time:

1. ✅ **Loads more files**: Detailed accomplishments doc will load first
2. ✅ **Loads Resume 2026 folder**: Case-insensitive matching will catch "Resume 2026"
3. ✅ **More content per file**: 20k chars instead of 15k
4. ✅ **More total content**: 100k chars instead of 80k
5. ✅ **Better extraction**: GPT will extract 6-8 bullets for Amazon role with comprehensive detail
6. ✅ **Reads thoroughly**: Explicit instructions to read ALL files for each role's details

## Testing Recommendation

Run the agent with the Microsoft TPM job again and check:
1. `debug_prompt.txt` should show more files loaded (including from Resume 2026/)
2. Output resume should have 6-8 detailed bullets for Amazon TPM role
3. Each bullet should showcase scope, impact, and technical complexity

## Rate Limit Note

With the increased content, you may hit the 30k TPM limit more often. The 65-second wait between calls should still work, but if you see rate limit errors, the code will tell you to move some files to `docs/archive/`.

---

## Additional Improvement: Skills Section Optimization

### Issue
Skills section was taking up too much space with old/irrelevant skills, leaving less room for impactful experience bullets.

### Changes Made

#### 1. **GPT Prompt - Aggressive Skills Filtering** (`resume_analyzer.py`)
- Changed from "COPY exactly from docs" to "ONLY include 10-15 most JD-relevant skills"
- Added explicit instruction: "Exclude outdated or tangential technologies"
- Focuses on: languages/tools mentioned in JD, transferable technical skills, key platforms/methodologies
- Skips: old programming languages, obsolete tools, anything not applicable to the specific job

#### 2. **Document Layout - Compact Skills Section** (`doc_generator.py`)
- Changed from **3-column table** (taking ~6-8 lines) to **single line, bullet-separated**
- Format: `Skill1 • Skill2 • Skill3 • ...`
- Saves ~5-7 lines of vertical space
- All that space now available for richer experience bullets

### Result
- Skills section: ~1 line instead of 6-8 lines
- More room for 6-8 detailed bullets per role
- Only shows skills directly relevant to the job
- Cleaner, more focused resume
