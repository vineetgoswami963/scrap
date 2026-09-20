import re


def matches_keywords(title, keywords):
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def is_too_senior(title, exclude_terms):
    title_lower = title.lower()
    for term in exclude_terms:
        pattern = r"\b" + re.escape(term.strip().lower()) + r"\b"
        if re.search(pattern, title_lower):
            return True
    return False


def filter_postings(postings, keywords, exclude_seniority_terms=None):
    matched = [p for p in postings if matches_keywords(p["title"], keywords)]
    if exclude_seniority_terms:
        matched = drop_senior(matched, exclude_seniority_terms)
    return matched


def drop_senior(postings, exclude_seniority_terms):
    if not exclude_seniority_terms:
        return postings
    return [p for p in postings if not is_too_senior(p["title"], exclude_seniority_terms)]
