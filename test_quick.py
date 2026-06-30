"""
Quick test with hardcoded Microsoft TPM job description
"""
import sys
import time
from resume_analyzer import load_docs_from_folder, compute_match, build_resume
from doc_generator import generate_word_resume

# Microsoft Senior TPM job description
JOB_DESCRIPTION = """
Senior Technical Program Manager - Microsoft Digital

Microsoft Digital (MSD) builds and manages the critical products and services that Microsoft runs on. 
We are hiring a Senior Technical Program Manager to drive tenant onboarding of Microsoft 365 services 
inside Microsoft's internal IT organization.

Responsibilities:
• Drive tenant onboarding programs of significant complexity end to end across multiple engineering teams
• Make ambiguous problem statements and turn them into structured programs
• Manage stakeholders across Microsoft 365 product engineering, internal business groups, security organizations
• Deliver in high stakes scenarios: keep work moving while managing risk, escalations, and tradeoffs
• Run program rhythms: status, milestone reviews, risk and issue management, dependency tracking
• Communicate clearly in writing and in meetings for engineers, business stakeholders, and senior leaders

Required Qualifications:
• Bachelor's Degree AND 4+ years experience in engineering, product/technical program management
• 2+ years of experience managing cross-functional and/or cross-team projects

Preferred Qualifications:
• Technical program management experience driving programs that span multiple engineering teams
• Track record of personally delivering complex programs to completion
• Stakeholder management experience across engineering, business, and operational audiences
• Technical fluency sufficient to understand engineering tradeoffs, dependencies, and risk
• Experience with Microsoft 365, multitenant SaaS, large enterprise IT, or cloud platform programs
• Background partnering with internal business groups, security engineering, compliance, or operations teams
• Experience bringing structure to new or unstructured program areas
"""

print("=" * 60)
print("   Testing Resume Builder - Quick Run")
print("=" * 60)

# Step 1: Load docs
print("\n[1/4] Loading documents...")
resume_docs = load_docs_from_folder("docs")

if not resume_docs.strip():
    print("[error] No documents loaded")
    sys.exit(1)

print(f"  ✓ Loaded {len(resume_docs)} chars from docs")

# Step 2: Compute match
print("\n[2/4] Computing match score...")
print("  (waiting 5 seconds before GPT call...)")
time.sleep(5)

try:
    match_result = compute_match(JOB_DESCRIPTION, resume_docs)
    print("\n" + "=" * 60)
    print("   MATCH ANALYSIS")
    print("=" * 60)
    print(f"  Match:          {match_result['match_pct']}%")
    print(f"  Rating:         {match_result['rating']}")
    print(f"  Recommendation: {match_result['recommendation']}")
    print(f"\n  Summary:")
    print(f"    {match_result['summary']}")
    print(f"\n  Strengths (top 5):")
    for s in match_result.get('strengths', [])[:5]:
        print(f"    ✓ {s}")
    print(f"\n  Gaps (top 5):")
    for g in match_result.get('gaps', [])[:5]:
        print(f"    ✗ {g}")
    print(f"\n  Missing Keywords:")
    kw_list = ', '.join(match_result.get('missing_keywords', [])[:15])
    print(f"    {kw_list}")
    print("=" * 60)
    
    missing_kw = match_result.get('missing_keywords', [])
    
except Exception as e:
    print(f"[error] Match analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Build resume
print("\n[3/4] Building tailored resume...")
print("  (waiting 65 seconds before next GPT call to avoid rate limit...)")
time.sleep(65)

try:
    result = build_resume(JOB_DESCRIPTION, resume_docs, missing_kw)
    
    print(f"\n  ✓ Resume built successfully")
    print(f"  Estimated ATS Score: {result.get('ats_score_estimate', 'N/A')}")
    
    # Generate Word doc
    resume_data = result.get('tailored_resume', {})
    
    print("\n[4/4] Generating Word document...")
    filepath = generate_word_resume(resume_data, "output")
    
    print(f"\n" + "=" * 60)
    print(f"   ✅ SUCCESS!")
    print("=" * 60)
    print(f"  File:       {filepath}")
    print(f"  ATS Score:  {result.get('ats_score_estimate', 'N/A')}")
    
    # Show experience bullet count to verify improvements
    experience = resume_data.get('experience', [])
    if experience:
        print(f"\n  📊 Experience Bullets (checking improvements):")
        for i, job in enumerate(experience[:4], 1):
            bullets = len(job.get('bullets', []))
            title = job.get('title', 'Unknown')[:40]
            company = job.get('company', '')[:20]
            print(f"    {i}. {title} @ {company}: {bullets} bullets")
            if i == 1:  # Check latest role
                if bullets >= 6:
                    print(f"       ✅ Latest role has {bullets} bullets (target: 6-8)")
                else:
                    print(f"       ⚠️  Latest role only has {bullets} bullets (expected 6-8)")
    
    # Show skills to verify compression
    skills = resume_data.get('skills', [])
    print(f"\n  🎯 Skills: {len(skills)} selected")
    if skills:
        skills_preview = ', '.join(skills[:8])
        if len(skills) > 8:
            skills_preview += f", ... (+{len(skills)-8} more)"
        print(f"    {skills_preview}")
        if len(skills) <= 15:
            print(f"    ✅ Skills count is {len(skills)} (target: 10-15)")
        else:
            print(f"    ⚠️  Skills count is {len(skills)} (expected 10-15)")
    
    # Show suggestions
    suggestions = result.get('suggestions', [])
    if suggestions:
        print(f"\n  💡 Suggestions:")
        for sug in suggestions[:3]:
            print(f"    • {sug}")
    
    print("=" * 60)
    print("\n  Open the file to see the improved resume with:")
    print("    ✓ Compact 1-line skills section")
    print("    ✓ 6-8 detailed bullets for latest role")
    print("    ✓ More space for experience content")
    
except Exception as e:
    print(f"[error] Resume building failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
