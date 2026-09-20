"""
Direct API adapters for the most common ATS (applicant tracking system)
platforms. These hit clean JSON endpoints instead of scraping HTML, so
they're far more reliable than generic scraping — use them whenever a
company's career site is hosted on one of these platforms.

Each adapter returns dicts of: company, title, url, description
(description is the full posting text where the platform provides it
inline; used for the years-of-experience check in scraper/experience.py).
"""
import re
import requests

from scraper.textutils import clean_text, html_to_text

HEADERS = {"User-Agent": "Mozilla/5.0 (job-scraper-bot; personal use)"}
TIMEOUT = 15


def _slug_from_url(url):
    """Pulls the company slug off the end of a board URL, e.g.
    https://boards.greenhouse.io/stripe -> 'stripe'"""
    return url.rstrip("/").split("/")[-1]


def fetch_greenhouse(company_name, url):
    slug = _slug_from_url(url)
    api = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = requests.get(api, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return [
        {
            "company": company_name,
            "title": clean_text(j["title"]),
            "url": j["absolute_url"],
            "description": html_to_text(j.get("content")),
        }
        for j in data.get("jobs", [])
    ]


def fetch_lever(company_name, url):
    slug = _slug_from_url(url)
    api = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = requests.get(api, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    results = []
    for j in data:
        desc = j.get("descriptionPlain") or html_to_text(j.get("description"))
        results.append(
            {
                "company": company_name,
                "title": clean_text(j["text"]),
                "url": j["hostedUrl"],
                "description": clean_text(desc),
            }
        )
    return results


def fetch_smartrecruiters(company_name, url):
    # Note: the list endpoint doesn't include full description text (only
    # the per-posting detail endpoint does, which would mean one extra
    # HTTP call per posting). Skipped for now to keep runs fast — these
    # postings just always get "YOE not stated" and pass the experience
    # filter unfiltered. Say the word if you want that added.
    slug = _slug_from_url(url)
    api = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    r = requests.get(api, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    results = []
    for j in data.get("content", []):
        job_url = f"https://jobs.smartrecruiters.com/{slug}/{j['id']}"
        results.append(
            {
                "company": company_name,
                "title": clean_text(j["name"]),
                "url": job_url,
                "description": None,
            }
        )
    return results


def fetch_ashby(company_name, url):
    slug = _slug_from_url(url)
    api = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = requests.get(api, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    results = []
    for j in data.get("jobs", []):
        desc = html_to_text(j.get("descriptionHtml")) if j.get("descriptionHtml") else None
        results.append(
            {
                "company": company_name,
                "title": clean_text(j["title"]),
                "url": j.get("jobUrl") or j.get("applyUrl"),
                "description": desc,
            }
        )
    return results


# Matches e.g. https://capitalone.wd12.myworkdayjobs.com/en-US/Capital_One
# or https://cisco.wd5.myworkdayjobs.com/Cisco_Careers
WORKDAY_URL_RE = re.compile(
    r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[\w-]+/)?([\w-]+)",
    re.IGNORECASE,
)


def _parse_workday_url(url):
    m = WORKDAY_URL_RE.search(url)
    if not m:
        return None
    tenant, wd_host, site = m.groups()
    return tenant, wd_host, site


def fetch_workday(company_name, url):
    """Workday's job-search widget calls a JSON endpoint under the hood —
    same idea as the other adapters, no browser rendering needed. Note:
    some Workday tenants sit behind Akamai/bot-detection and may reject
    this; those fall through to an empty result like any other failure."""
    parsed = _parse_workday_url(url)
    if not parsed:
        return []
    tenant, wd_host, site = parsed
    api = f"https://{tenant}.{wd_host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"

    results = []
    offset = 0
    limit = 20
    while True:
        body = {"limit": limit, "offset": offset, "searchText": ""}
        r = requests.post(
            api,
            json=body,
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break

        for j in postings:
            path = j.get("externalPath", "")
            job_url = f"https://{tenant}.{wd_host}.myworkdayjobs.com{path}" if path else url
            results.append(
                {
                    "company": company_name,
                    "title": clean_text(j.get("title", "")),
                    "url": job_url,
                    # Workday's list endpoint doesn't include full
                    # description text either (detail endpoint would, at
                    # the cost of one extra call per posting) — always
                    # comes through as "YOE not stated".
                    "description": None,
                }
            )

        total = data.get("total", 0)
        offset += limit
        if offset >= total or offset > 500:  # safety cap either way
            break

    return results


def fetch_amazon(company_name, url):
    """Amazon's careers site isn't on any ATS above, but its own search
    page calls a plain endpoint under the hood — same idea, just
    Amazon-specific and undocumented (their frontend uses it, not an
    official public API). Confirmed against public examples of this same
    endpoint; if Amazon changes its shape, this fails quietly like
    anything else rather than crashing the run."""
    api = "https://www.amazon.jobs/en/search.json"
    results = []
    offset = 0
    limit = 100

    while True:
        params = {
            "base_query": "",
            "offset": offset,
            "result_limit": limit,
            "sort": "recent",
        }
        r = requests.get(api, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])
        if not jobs:
            break

        for j in jobs:
            path = j.get("job_path", "")
            job_url = f"https://www.amazon.jobs{path}" if path else url
            desc = j.get("description_short")
            results.append(
                {
                    "company": company_name,
                    "title": clean_text(j.get("title", "")),
                    "url": job_url,
                    "description": clean_text(desc) if desc else None,
                }
            )

        total = data.get("hits", 0)
        offset += limit
        if offset >= total or offset > 1000:  # safety cap
            break

    return results


ADAPTERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "smartrecruiters": fetch_smartrecruiters,
    "ashby": fetch_ashby,
    "workday": fetch_workday,
    "amazon": fetch_amazon,
}

DETECT_PATTERNS = {
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "smartrecruiters.com": "smartrecruiters",
    "ashbyhq.com": "ashby",
    "myworkdayjobs.com": "workday",
    "amazon.jobs": "amazon",
}


def detect_type(url):
    for pattern, ats_type in DETECT_PATTERNS.items():
        if pattern in url:
            return ats_type
    return "generic"
