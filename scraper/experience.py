"""
Best-effort read of the minimum years-of-experience a posting asks for,
pulled from its full description text (not just the title — most postings
never put a number in the title at all).

This is a heuristic, not a guarantee: some postings state YOE in a way this
regex won't catch, and plenty of genuine entry-level roles never state a
number at all. Those get treated as a pass, not a drop — see
passes_experience_filter.
"""
import re

YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)\s*(?:of\s+)?"
    r"(?:relevant\s+|professional\s+|prior\s+)?experience",
    re.IGNORECASE,
)

ENTRY_LEVEL_PHRASES = [
    "no prior experience",
    "no experience required",
    "no experience necessary",
    "entry level",
    "entry-level",
    "fresher",
    "new grad",
    "recent graduate",
    "0 years of experience",
]


def extract_min_years_required(description_text):
    if not description_text:
        return None

    text = description_text.lower()

    if any(phrase in text for phrase in ENTRY_LEVEL_PHRASES):
        return 0

    matches = YEARS_PATTERN.findall(text)
    if not matches:
        return None

    lows = [int(m[0]) for m in matches]
    return min(lows)


def passes_experience_filter(description_text, max_years):
    """Returns (keep: bool, note: str for the email)."""
    required = extract_min_years_required(description_text)
    if required is None:
        return True, "YOE not stated"
    if required <= max_years:
        return True, f"~{required}+ yrs stated"
    return False, f"~{required}+ yrs stated"
