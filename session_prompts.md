# Job Agent — Build Session Prompts

## Initial Build
- Build an agent that:
  1. Asks for a job link
  2. Reads the job description from that link
  3. Compares it to my resume and other docs in a folder
  4. Suggests changes to reach ATS score of 85 and above
  5. Creates a Word doc resume matching the job description and suggests downloading it

## API & Config
- How to install pip for this?
- Where is my API key?
- Change to Claude
- Change back to OpenAI
- Do not consider resume with John Doe

## Folder & File Handling
- The code is built to read RESUME folder → change back to docs
- Make a note that docs has more folders and subfolders in it
- The agent skipped my "Resume 2026" folder which has more skills and experience of my current job
- Which file has those projects? (Nano Internet, Mobile Center)
- Put a pin on that, I will make it cleaner

## Agent Flow Changes
- Add one more step: analyse and share the ATS score and show if I am a good or bad match before preparing my resume
- Add the first step to scrub the web for matching my job experience from the docs folder
- Remove the web search part for now
- Remove ATS scoring and compare files in docs to job description and show percentage of matching before building a resume
- No, not direct comparison — smart comparison
- And then in the end, build a resume with ATS score of 85 and above

## Resume Quality
- The quality of the resume is bad. Not using my experiences from the docs folder. Don't just match to job description. Modify the resume to make it personalised and correct formatting issues
- The code is ignoring my docs folder. It says there is no match where there is ample experience
- Education from every resume should be the same, not make new false information
- Content on experience is something I actually did — refer from all my resumes but rephrase it to be relatable to the job description. Not add new false information
- Also, not add new stuff in skills. Keep it like you found in the docs and not add new stuff to match the job description

## Date / Content Filters
- Ignore all information before 2014 (experience only, keep education)
- Change 2014 to 2015
- Ignore jobs and projects before 2015, keep education
- Remove projects "Nano Internet" and "Mobile Center"

## Formatting
- Change to a narrow page layout, a bit tighter
- Make certificates 2-column bullets
- Now you have more space — add more substance from my experience (4-6 bullets per role)

## Bug Fixes & Errors Resolved
- 429 token limit error → added 65 second wait between GPT calls, reduced doc budget
- GPT returned empty content → removed response_format json_object, parse manually
- GPT refused request → detected JS-only sites (Microsoft, LinkedIn) upfront, skip scraping and go to paste mode
- UnboundLocalError on system_prompt → moved debug block to after prompt definitions
- ATS score returning 0 → replaced GPT scoring with semantic smart comparison
