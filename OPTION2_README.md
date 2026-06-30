# Resume Builder - Option 2: Two-Step Workflow

## What's Different?

**Option 1** (original `app.py`): Automatically builds resume after match analysis  
**Option 2** (new `app_option2.py`): Shows match analysis FIRST, then lets you decide whether to build resume

## Features

### Two-Step Process:

**Step 1: Calculate ATS & Match Analysis**
- Upload your resume documents
- Paste job description or URL
- Click "Calculate ATS Score & Match Analysis"
- See detailed match report:
  - Match percentage (0-100%)
  - Rating (Strong Match, Good Match, etc.)
  - Your strengths for this role
  - Gaps you need to address
  - Missing keywords from JD
  - Recommendation (Go Ahead / Proceed with Caution / Not Recommended)

**Step 2: Decide & Build**
- Review the match analysis
- If good match → Click "Build Tailored Resume"
- If poor match → Click "Cancel" and try different job
- Saves you 65 seconds + GPT tokens if you decide not to proceed!

## How to Run

### Start the Server:
```bash
cd "c:\Users\pradn\AI projects"
python app_option2.py
```

### Open in Browser:
```
http://localhost:5001
```

Note: Runs on **port 5001** (Option 1 uses port 5000) so you can run both simultaneously if needed.

## Why Use Option 2?

### Advantages:
✅ **See before you commit** - Review match quality before spending time on resume generation  
✅ **Save time** - Don't build resume for jobs that are poor matches  
✅ **Save money** - Avoid unnecessary GPT API calls for unsuitable jobs  
✅ **Make informed decisions** - Full match report helps you decide  
✅ **Better workflow** - Natural decision point after seeing strengths/gaps

### Best For:
- Applying to multiple jobs and want to filter by match quality first
- Want to see gaps before creating resume
- Testing different job descriptions to find best fit
- Budget-conscious (want to avoid unnecessary API calls)

## Workflow Comparison

### Option 1 (Auto):
```
Upload → Job Description → Generate Resume (automatic)
                            ↓
                     Match Report + Resume Download
```

### Option 2 (Manual):
```
Upload → Job Description → Calculate ATS
                            ↓
                     Match Report
                            ↓
                    [User Decision Point]
                            ↓
              Build Resume? (Yes/No)
                            ↓
                   Resume Download (if Yes)
```

## Technical Details

### Files Created:
- `app_option2.py` - Flask backend with two-step workflow
- `templates/index_option2.html` - Two-step UI
- `static/style_option2.css` - Styling for Option 2
- `static/app_option2.js` - JavaScript for two-step flow

### Key Differences from Option 1:
1. **Separate endpoints**: `/calculate-ats` and `/build-resume` instead of single `/run`
2. **Match caching**: Stores match results so resume building can reuse them
3. **Decision UI**: Shows match results with clear "Build" or "Cancel" buttons
4. **Better UX**: User stays in control of the process

## Ports

- **Option 1**: http://localhost:5000
- **Option 2**: http://localhost:5001

You can run both at the same time!

## What Gets Built?

When you click "Build Tailored Resume", you get the same improvements as the command-line version:
- ✅ Two separate Amazon roles (Enterprise Engineering & RME)
- ✅ AI Projects section with personal AI projects only
- ✅ 2-line skills section (16-20 relevant skills, prioritized)
- ✅ 6-8 bullets for latest role, 5-6 for others
- ✅ Justified text alignment
- ✅ Timestamped filename
- ✅ No location in contact info
- ✅ All work experience from 2015 onwards

## Example Usage

1. **Start the server**: `python app_option2.py`
2. **Open browser**: Go to http://localhost:5001
3. **Upload docs** (optional - uses existing `docs/` folder)
4. **Paste job description**
5. **Click "Calculate ATS Score"** - Wait ~15 seconds
6. **Review match report**:
   - If 70%+ match → Click "Build Tailored Resume"
   - If <50% match → Click "Cancel" and try different job
7. **Wait 65 seconds** for rate limit (if building resume)
8. **Download resume**

## When to Use Each Option

### Use Option 1 if:
- You're confident the job is a good match
- You want the fastest end-to-end workflow
- You don't need to review match analysis before building

### Use Option 2 if:
- You're evaluating multiple jobs and want to filter first
- You want to see strengths/gaps before committing
- You're on a budget and want to minimize API calls
- You prefer more control over the process

---

## Both Options Available!

You can use either workflow - they're both fully functional and use the same underlying resume generation code with all the latest improvements.
