"""
One-off diagnostic: renders a single company's career page exactly like
main.py's headless fallback does, but saves a screenshot and the full
rendered HTML so you can see what the browser actually got back —
a cookie-consent wall, a CAPTCHA, an iframe, or genuinely nothing.

Usage:
    python debug_playwright.py "Google"
    python debug_playwright.py "https://careers.google.com/jobs/results/"

Looks the name up in config/companies.yaml if it's not already a URL.
Output lands in debug/<company>.png and debug/<company>.html.
"""
import sys
from pathlib import Path

import yaml

from scraper.playwright_scraper import playwright_browser, fetch_with_playwright

BASE_DIR = Path(__file__).resolve().parent
DEBUG_DIR = BASE_DIR / "debug"


def resolve(arg):
    if arg.startswith("http"):
        return arg, arg

    companies_path = BASE_DIR / "config" / "companies.yaml"
    with open(companies_path, "r", encoding="utf-8") as f:
        companies = yaml.safe_load(f)["companies"]

    for c in companies:
        if c["name"].lower() == arg.lower():
            return c["name"], c["url"]

    print(f"No company named '{arg}' found in config/companies.yaml")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_playwright.py <company name or URL>")
        sys.exit(1)

    name, url = resolve(sys.argv[1])

    keywords_path = BASE_DIR / "config" / "keywords.yaml"
    with open(keywords_path, "r", encoding="utf-8") as f:
        keywords = yaml.safe_load(f)["keywords"]

    print(f"Rendering {name} ({url}) ...")
    with playwright_browser() as browser:
        results = fetch_with_playwright(
            browser, name, url, keywords, debug_dir=DEBUG_DIR
        )

    print(f"\n{len(results)} keyword-matching link(s) found.")
    for r in results[:10]:
        print(f"  - {r['title']}  ->  {r['url']}")

    print(f"\nOpen the screenshot in {DEBUG_DIR}/ to see exactly what the "
          f"headless browser rendered for {name}.")


if __name__ == "__main__":
    main()
