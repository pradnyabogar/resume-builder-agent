# Job Application Agent

Reads a job posting URL, compares it to your resume, scores ATS compatibility, suggests improvements, and generates a tailored Word resume.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...
   ```

3. Drop your resume and any other relevant docs into the `docs/` folder.
   Supported formats: `.pdf`, `.docx`, `.doc`, `.txt`

## Run

```
python agent.py
```

The agent will:
1. Ask for a job posting URL
2. Fetch and parse the job description
3. Read all docs in `./docs/`
4. Score your resume (ATS) and suggest changes to hit 85+
5. Generate a tailored `.docx` resume in `./output/`

## Output

Tailored resume is saved to `./output/<YourName>_Resume.docx`
