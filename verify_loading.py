"""
Quick verification that document loading improvements work
"""
from resume_analyzer import load_docs_from_folder

print("=" * 70)
print("   VERIFYING DOCUMENT LOADING IMPROVEMENTS")
print("=" * 70)

print("\nLoading documents from ./docs/...")
print("-" * 70)

resume_docs = load_docs_from_folder("docs")

print("-" * 70)
print(f"\n✅ TOTAL LOADED: {len(resume_docs)} characters")

# Check what we're looking for
print("\n📋 Verification Checklist:")

# Check 1: Priority files loaded
checks = {
    "Pradnya_Bogar_Accomplishments.docx": "accomplishments" in resume_docs.lower(),
    "Pradnya_Bogar_Complete_Work_Record.docx": "complete_work_record" in resume_docs.lower() or "complete work record" in resume_docs.lower(),
    "Resume 2026 folder files": "resume 2026" in resume_docs.lower() or "resume2026" in resume_docs.lower(),
}

for name, found in checks.items():
    status = "✅" if found else "❌"
    print(f"  {status} {name}: {'Found' if found else 'NOT FOUND'}")

# Check 2: Character count
char_target = 80000
if len(resume_docs) >= char_target:
    print(f"  ✅ Character count: {len(resume_docs):,} chars (target: {char_target:,}+)")
else:
    print(f"  ⚠️  Character count: {len(resume_docs):,} chars (target: {char_target:,}+)")

# Check 3: Look for Amazon role details
amazon_indicators = [
    "amazon", "aws", "rme", "reliability maintenance",
    "operations", "$30m", "$2.1m", "women in engineering"
]
found_indicators = [ind for ind in amazon_indicators if ind.lower() in resume_docs.lower()]
print(f"  ✅ Amazon role indicators found: {len(found_indicators)}/{len(amazon_indicators)}")
if found_indicators:
    print(f"     Found: {', '.join(found_indicators[:5])}")

print("\n" + "=" * 70)
if len(resume_docs) >= 80000 and len(found_indicators) >= 4:
    print("✅ IMPROVEMENTS WORKING: More documents loaded with richer content!")
else:
    print("⚠️  Improvements may not be fully working. Check console output above.")
print("=" * 70)

# Show first 500 chars as preview
print("\n📄 Content Preview (first 500 chars):")
print("-" * 70)
print(resume_docs[:500])
print("...")
print("-" * 70)
