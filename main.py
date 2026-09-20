import sys
import time
import logging
from pathlib import Path

import yaml
from dotenv import load_dotenv

from scraper.ats_adapters import ADAPTERS, detect_type
from scraper.generic_scraper import fetch_generic
from scraper.filters import filter_postings, drop_senior
from scraper.experience import passes_experience_filter
from scraper.db import init_db, filter_new
from scraper.notifier import send_email_digest

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("job-scraper")

# Be polite between requests to any single generic site.
REQUEST_DELAY_SECONDS = 1.0

# Set to False to skip the headless-browser fallback entirely and only use
# known ATS APIs + plain static HTML scraping.
USE_PLAYWRIGHT_FALLBACK = True

# Flips to False the first time Playwright turns out not to be installed,
# so we log the "run pip install playwright..." warning once instead of
# once per company.
_playwright_available = True


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def scrape_company(company, keywords, exclude_seniority_terms, browser=None):
    global _playwright_available

    name = company["name"]
    url = company["url"]
    ats_type = company.get("type") or detect_type(url)

    try:
        if ats_type in ADAPTERS:
            # Known ATS (Greenhouse/Lever/SmartRecruiters/Ashby/Workday) —
            # this is real data straight from their API, so however many
            # results come back, that's the real answer. No fallback needed.
            postings = ADAPTERS[ats_type](name, url)
            return filter_postings(postings, keywords, exclude_seniority_terms)

        # Unknown platform — try the fast static-HTML path first.
        postings = fetch_generic(name, url, keywords)
        if postings:
            return drop_senior(postings, exclude_seniority_terms)

        # Static HTML came back empty. Could genuinely be zero matching
        # roles right now — or (very commonly) the page is JS-rendered and
        # the real listings just aren't in that initial HTML at all.
        # Escalate to an actual browser as a last resort.
        if USE_PLAYWRIGHT_FALLBACK and _playwright_available and browser is not None:
            log.info(f"{name}: static scrape found nothing, trying headless render...")
            from scraper.playwright_scraper import fetch_with_playwright

            rendered = fetch_with_playwright(browser, name, url, keywords)
            return drop_senior(rendered, exclude_seniority_terms)

        return []

    except ImportError:
        _playwright_available = False
        log.warning(
            "Playwright not installed — headless-browser fallback disabled "
            "for the rest of this run. To enable it: "
            "pip install playwright && playwright install chromium"
        )
        return []
    except Exception as e:
        log.warning(f"Failed scraping {name} ({url}): {e}")
        return []


def apply_experience_filter(postings, max_years):
    kept = []
    dropped_count = 0
    for p in postings:
        keep, note = passes_experience_filter(p.get("description"), max_years)
        if keep:
            p["yoe_note"] = note
            kept.append(p)
        else:
            dropped_count += 1
    return kept, dropped_count


def main():
    companies_path = BASE_DIR / "config" / "companies.yaml"
    if not companies_path.exists():
        log.error(
            "config/companies.yaml not found. Copy config/companies.example.yaml "
            "to config/companies.yaml and fill in your company list."
        )
        sys.exit(1)

    companies = load_yaml(companies_path)["companies"]
    keywords = load_yaml(BASE_DIR / "config" / "keywords.yaml")["keywords"]
    exclude_seniority_terms = load_yaml(BASE_DIR / "config" / "seniority.yaml")[
        "exclude_terms"
    ]
    experience_cfg = load_yaml(BASE_DIR / "config" / "experience.yaml")
    max_years = experience_cfg.get("max_years", 1)

    init_db()

    all_matches = []
    total_dropped_for_experience = 0

    browser_cm = None
    browser = None
    if USE_PLAYWRIGHT_FALLBACK:
        try:
            from scraper.playwright_scraper import playwright_browser

            browser_cm = playwright_browser()
            browser = browser_cm.__enter__()
        except ImportError:
            log.warning(
                "Playwright not installed — headless-browser fallback disabled "
                "for this run. To enable it: "
                "pip install playwright && playwright install chromium"
            )

    try:
        for i, company in enumerate(companies):
            role_matches = scrape_company(
                company, keywords, exclude_seniority_terms, browser
            )
            exp_matches, dropped = apply_experience_filter(role_matches, max_years)
            total_dropped_for_experience += dropped

            log.info(
                f"{company['name']}: {len(exp_matches)} matching posting(s) "
                f"(dropped {dropped} for exceeding {max_years} yr experience cap)"
            )
            all_matches.extend(exp_matches)

            if i < len(companies) - 1:
                time.sleep(REQUEST_DELAY_SECONDS)
    finally:
        if browser_cm is not None:
            browser_cm.__exit__(None, None, None)

    new_matches = filter_new(all_matches)
    log.info(
        f"Total new matches this run: {len(new_matches)} "
        f"(experience filter dropped {total_dropped_for_experience} across all companies)"
    )

    if new_matches:
        try:
            send_email_digest(new_matches)
            log.info("Email digest sent.")
        except Exception as e:
            log.error(f"Failed to send email: {e}")
    else:
        log.info("No new matches — no email sent.")


if __name__ == "__main__":
    main()
