import re
from bs4 import BeautifulSoup


def clean_text(text):
    """Strip non-breaking spaces, zero-width chars, and collapse whitespace.
    Scraped HTML very commonly contains \\xa0 (from &nbsp;) which crashes
    plain-ASCII email encoding if it isn't normalized out."""
    if not text:
        return text
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\u2028", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def html_to_text(html):
    """Strip an HTML job-description body down to clean plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return clean_text(text)
