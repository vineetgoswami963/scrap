import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_jobs (
            url TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            first_seen TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def filter_new(postings):
    """Takes a list of {company, title, url} dicts. Returns only the ones
    never seen before, and records them so they won't be flagged again."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    new_postings = []
    now = datetime.now(timezone.utc).isoformat()

    for p in postings:
        cur.execute("SELECT 1 FROM seen_jobs WHERE url = ?", (p["url"],))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO seen_jobs (url, company, title, first_seen) VALUES (?, ?, ?, ?)",
                (p["url"], p["company"], p["title"], now),
            )
            new_postings.append(p)

    conn.commit()
    conn.close()
    return new_postings
