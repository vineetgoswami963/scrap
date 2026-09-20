"""
Best-effort scraper for plain HTML career pages that aren't on a known ATS.
Scans every link's visible text + href for keyword matches.

Limitation: this only sees what's in the initial HTML response. Career
pages built as a React/Angular single-page app (content loaded via JS
after the page loads) won't yield results here — those need a headless
browser (Playwright) to render first. Worth adding later if you find a
chunk of your 100+ companies fall in that bucket.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper.textutils import clean_text

HEADERS = {"User-Agent": "Mozilla/5.0 (job-scraper-bot; personal use)"}
TIMEOUT = 15


def fetch_generic(company_name, url, keywords):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        text = clean_text(a.get_text(strip=True))
        href = a["href"]
        haystack = f"{text} {href}".lower()
        if any(kw.lower() in haystack for kw in keywords):
            full_url = urljoin(url, href)
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                results.append(
                    {
                        "company": company_name,
                        "title": text or "(untitled link — check URL)",
                        "url": full_url,
                        "description": None,
                    }
                )
    return results
