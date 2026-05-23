import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_profile_summary(resume_docs: str) -> dict:
    """Use GPT to extract a concise profile from the candidate's docs."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract a concise candidate profile from the provided documents. "
                    "Respond with valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": f"""CANDIDATE DOCUMENTS:
{resume_docs}

Return this JSON:
{{
  "job_titles": ["<most likely job titles this person would apply for, up to 4>"],
  "top_skills": ["<top 8 skills>"],
  "years_experience": "<e.g. 5 years>",
  "industry": "<primary industry>",
  "search_query": "<a Google-style job search query based on their profile, e.g. 'Senior Data Engineer Python AWS jobs 2024'>"
}}""",
            },
        ],
        temperature=0.3,
        max_tokens=500,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content.strip())


def search_jobs(query: str, num_results: int = 8) -> list[dict]:
    """
    Search for jobs using Google search scraping.
    Returns a list of {title, url, snippet} dicts.
    """
    search_url = "https://www.google.com/search"
    params = {"q": query, "num": num_results}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Search failed: {e}")

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    for g in soup.select("div.g"):
        title_el = g.select_one("h3")
        link_el = g.select_one("a")
        snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")

        title = title_el.get_text(strip=True) if title_el else ""
        url = link_el["href"] if link_el and link_el.get("href", "").startswith("http") else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        if title and url:
            results.append({"title": title, "url": url, "snippet": snippet})

        if len(results) >= num_results:
            break

    return results


def find_matching_jobs(resume_docs: str) -> tuple[list[dict], dict]:
    """
    Extract profile from docs, search for matching jobs.
    Returns (job_results, profile).
    """
    profile = extract_profile_summary(resume_docs)
    query = profile.get("search_query", "software engineer jobs")
    jobs = search_jobs(query)
    return jobs, profile
