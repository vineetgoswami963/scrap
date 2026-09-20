# import logging
# import contextlib
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# logger = logging.getLogger(__name__)

# @contextlib.contextmanager
# def playwright_browser(headless=True):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=headless)
#         try:
#             yield browser
#         finally:
#             browser.close()

# def fetch_with_playwright(*args, **kwargs) -> str:
#     """
#     Accepts arbitrary arguments from main.py and automatically finds 
#     the target URL and the Playwright browser instance.
#     """
#     html_content = ""
#     url = None
#     browser = None
#     max_scrolls = 4
    
#     # Dynamically extract just what we need from the 4 arguments main.py sends
#     for arg in args:
#         if isinstance(arg, str) and arg.startswith("http"):
#             url = arg
#         elif hasattr(arg, 'new_context'):
#             browser = arg

#     if not url or not browser:
#         logger.error(f"Playwright missing URL or browser in args: {args}")
#         return ""

#     # Set up the anti-bot browser window
#     context = browser.new_context(
#         viewport={'width': 1920, 'height': 1080},
#         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     )
#     page = context.new_page()

#     try:
#         logger.info(f"Playwright routing to {url}...")
        
#         # Wait for Big Tech SPA frameworks to finish firing network requests
#         page.goto(url, wait_until="networkidle", timeout=45000)
#         page.wait_for_timeout(3000)

#         for i in range(max_scrolls):
#             logger.debug(f"Scrolling page {i + 1} of {max_scrolls}...")
            
#             # Scroll down to trigger lazy-loaded job cards
#             page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#             page.wait_for_timeout(2500)

#             # Common ATS 'Next' and 'Load More' buttons
#             pagination_selectors = [
#                 "button[aria-label*='Next']",
#                 "button[aria-label*='next']",
#                 "a[aria-label*='Next']",
#                 "button:has-text('Load more')",
#                 "button:has-text('Show more')",
#                 "a:has-text('Next')",
#                 ".pagination-next"
#             ]
            
#             for selector in pagination_selectors:
#                 try:
#                     element = page.query_selector(selector)
#                     if element and element.is_visible():
#                         element.click(timeout=3000)
#                         logger.debug(f"Clicked pagination button: {selector}")
#                         page.wait_for_timeout(3000)
#                         break
#                 except Exception:
#                     pass
                    
#         # Final wait for the very last batch of jobs to render
#         page.wait_for_timeout(2000)
#         html_content = page.content()
        
#     except PlaywrightTimeoutError:
#         logger.error(f"Playwright Timeout: Took too long to load {url}")
#     except Exception as e:
#         logger.error(f"Playwright Error while scraping {url}: {str(e)}")
#     finally:
#         context.close()
        
#     return html_content


# import logging
# import contextlib
# from urllib.parse import urljoin
# from bs4 import BeautifulSoup
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# logger = logging.getLogger(__name__)

# @contextlib.contextmanager
# def playwright_browser(headless=True):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=headless)
#         try:
#             yield browser
#         finally:
#             browser.close()

# def _parse_rendered_html(html: str, base_url: str, keywords=None) -> list:
#     """
#     Parses rendered HTML into a list of job dicts matching main.py's expected schema.
#     """
#     # 1. Try delegating to project's generic_scraper if available
#     try:
#         from scraper import generic_scraper
#         for func_name in ["parse_jobs_from_html", "extract_jobs", "parse_generic_html", "scrape_generic_page"]:
#             if hasattr(generic_scraper, func_name):
#                 func = getattr(generic_scraper, func_name)
#                 try:
#                     res = func(html, base_url, keywords)
#                     if res and isinstance(res, list):
#                         return res
#                 except Exception:
#                     pass
#     except Exception:
#         pass

#     # 2. Built-in DOM fallback parser for Big Tech SPAs
#     soup = BeautifulSoup(html, "html.parser")
#     found_jobs = []
#     seen_urls = set()

#     for a in soup.find_all("a", href=True):
#         href = a["href"].strip()
#         full_url = urljoin(base_url, href)
        
#         # Look for job links and cards
#         is_job_link = any(pattern in href.lower() for pattern in [
#             "/job/", "/jobs/", "/posting/", "/careers/", "/viewjob", "jobid=", "req_id="
#         ])
        
#         # Grab title text from link or nested headings
#         title_text = ""
#         heading = a.find(["h1", "h2", "h3", "h4", "span", "p"])
#         if heading and len(heading.get_text(strip=True)) > 4:
#             title_text = heading.get_text(strip=True)
#         else:
#             title_text = a.get_text(strip=True)
            
#         aria_label = a.get("aria-label", "")
#         if aria_label and len(aria_label) > len(title_text):
#             title_text = aria_label

#         if is_job_link and full_url not in seen_urls and len(title_text) > 3:
#             # Exclude navigation/privacy/footer links
#             if not any(skip in title_text.lower() for skip in ["privacy", "terms", "cookie", "home", "about us", "sign in", "next", "previous"]):
#                 seen_urls.add(full_url)
#                 found_jobs.append({
#                     "title": title_text,
#                     "url": full_url,
#                     "location": "India",
#                     "text": a.parent.get_text(" ", strip=True) if a.parent else title_text
#                 })

#     return found_jobs


# def fetch_with_playwright(*args, **kwargs) -> list:
#     """
#     Navigates via Playwright, scrolls, and returns a list[dict] of matching jobs.
#     """
#     url = None
#     browser = None
#     keywords = None
#     max_scrolls = 4
    
#     for arg in args:
#         if isinstance(arg, str) and arg.startswith("http"):
#             url = arg
#         elif hasattr(arg, "new_context"):
#             browser = arg
#         elif isinstance(arg, (list, set)):
#             keywords = arg

#     if not url or not browser:
#         logger.error(f"Playwright missing URL or browser in args: {args}")
#         return []

#     context = browser.new_context(
#         viewport={"width": 1920, "height": 1080},
#         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     )
#     page = context.new_page()
#     jobs = []

#     try:
#         logger.info(f"Playwright routing to {url}...")
#         page.goto(url, wait_until="networkidle", timeout=45000)
#         page.wait_for_timeout(3000)

#         for i in range(max_scrolls):
#             page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#             page.wait_for_timeout(2500)

#             pagination_selectors = [
#                 "button[aria-label*='Next']",
#                 "button[aria-label*='next']",
#                 "a[aria-label*='Next']",
#                 "button:has-text('Load more')",
#                 "button:has-text('Show more')",
#                 "a:has-text('Next')",
#                 ".pagination-next"
#             ]
#             for selector in pagination_selectors:
#                 try:
#                     element = page.query_selector(selector)
#                     if element and element.is_visible():
#                         element.click(timeout=3000)
#                         page.wait_for_timeout(3000)
#                         break
#                 except Exception:
#                     pass

#         page.wait_for_timeout(2000)
#         html_content = page.content()
#         jobs = _parse_rendered_html(html_content, url, keywords)

#     except PlaywrightTimeoutError:
#         logger.error(f"Playwright Timeout: Took too long to load {url}")
#     except Exception as e:
#         logger.error(f"Playwright Error while scraping {url}: {str(e)}")
#     finally:
#         context.close()

#     return jobs



import logging
import contextlib
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def playwright_browser(headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            yield browser
        finally:
            browser.close()

def _extract_job_data(html: str, base_url: str, company_name: str) -> list:
    """
    Converts raw HTML into the list of job dictionaries required by main.py and db.py.
    """
    soup = BeautifulSoup(html, "html.parser")
    found_jobs = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_url, href)
        
        is_job_link = any(pattern in href.lower() for pattern in [
            "/job/", "/jobs/", "/posting/", "/careers/", "/viewjob", "jobid=", "req_id="
        ])
        
        if not is_job_link or full_url in seen_urls:
            continue
            
        title_text = ""
        heading = a.find(["h1", "h2", "h3", "h4", "span", "p"])
        if heading and len(heading.get_text(strip=True)) > 4:
            title_text = heading.get_text(strip=True)
        else:
            title_text = a.get_text(strip=True)
            
        aria_label = a.get("aria-label", "")
        if aria_label and len(aria_label) > len(title_text):
            title_text = aria_label

        if len(title_text) > 3 and not any(skip in title_text.lower() for skip in ["privacy", "terms", "cookie"]):
            seen_urls.add(full_url)
            
            # --- THE FIX: We added "company" so db.py can save it! ---
            found_jobs.append({
                "title": title_text,
                "url": full_url,
                "company": company_name, 
                "location": "India",
                "text": a.parent.get_text(" ", strip=True) if a.parent else title_text
            })

    return found_jobs

def fetch_with_playwright(*args, **kwargs) -> list:
    url = None
    browser = None
    company_name = "Unknown Company"
    max_scrolls = 4
    
    # Intelligently figure out which argument is the URL and which is the Company Name
    for arg in args:
        if hasattr(arg, "new_context"):
            browser = arg
        elif isinstance(arg, str):
            if arg.startswith("http"):
                url = arg
            else:
                company_name = arg

    if not url or not browser:
        logger.error(f"Playwright missing URL or browser in args: {args}")
        return []

    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    jobs = []

    try:
        logger.info(f"Playwright routing to {url}...")
        page.goto(url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(3000)

        for i in range(max_scrolls):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2500)

            pagination_selectors = [
                "button[aria-label*='Next']", "button[aria-label*='next']",
                "a[aria-label*='Next']", "button:has-text('Load more')",
                "button:has-text('Show more')", "a:has-text('Next')", ".pagination-next"
            ]
            for selector in pagination_selectors:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        element.click(timeout=3000)
                        page.wait_for_timeout(3000)
                        break
                except Exception:
                    pass

        page.wait_for_timeout(2000)
        
        # Pass the extracted company_name into our parser
        jobs = _extract_job_data(page.content(), url, company_name)

    except PlaywrightTimeoutError:
        logger.error(f"Playwright Timeout: Took too long to load {url}")
    except Exception as e:
        logger.error(f"Playwright Error while scraping {url}: {str(e)}")
    finally:
        context.close()

    return jobs