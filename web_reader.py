import requests
from bs4 import BeautifulSoup

# Known job site patterns for targeted extraction
JOB_SITE_SELECTORS = [
    # Greenhouse
    {"id": "content"},
    # Lever
    {"class": "content"},
    # Workday
    {"data-automation-id": "jobPostingDescription"},
    # Indeed
    {"id": "jobDescriptionText"},
    # LinkedIn (partial — often blocked)
    {"class": "description__text"},
    # Generic fallbacks
    {"class": lambda c: c and any(
        kw in " ".join(c).lower()
        for kw in [
            "job-description", "jobdescription", "job_description",
            "posting-description", "job-detail", "job-content",
            "description", "job-body", "vacancy"
        ]
    )},
]


def fetch_job_description(url: str) -> tuple[str, str]:
    """
    Fetch job description from URL.
    Returns (text, warning) where warning is empty string if all good.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # Sites known to require JS rendering — skip scraping, go straight to paste
    JS_ONLY_DOMAINS = [
        "linkedin.com", "microsoft.com", "workday.com", "myworkdayjobs.com",
        "greenhouse.io", "lever.co", "smartrecruiters.com", "icims.com",
        "taleo.net", "successfactors.com", "careers.microsoft.com",
        "apply.careers.microsoft.com",
    ]
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    if any(d in domain for d in JS_ONLY_DOMAINS):
        return "", (
            f"This site ({domain}) requires JavaScript to load job content and cannot be scraped.\n"
            "  Please copy and paste the job description text manually."
        )

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch URL: {e}")

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    text = ""
    for sel in JOB_SITE_SELECTORS:
        el = soup.find(attrs=sel)
        if el:
            candidate = el.get_text(separator="\n", strip=True)
            if len(candidate) > 200:
                text = candidate
                break

    if not text:
        body = soup.find("body")
        text = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    # Detect if we got JS config instead of real content
    js_indicators = ['"navbarData"', '"themeOptions"', '"configPath"', 'varTheme', '__NEXT_DATA__']
    if any(indicator in text for indicator in js_indicators):
        return "", (
            "The page returned JavaScript configuration instead of job content — "
            "this site requires a browser to render.\n"
            "  Please copy and paste the job description text manually."
        )

    warning = ""
    if len(text) < 300:
        warning = (
            f"Only extracted {len(text)} characters — the site may block scraping. "
            "Try pasting the job description manually."
        )

    return text, warning
