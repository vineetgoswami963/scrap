# Job Scraper

Checks 100+ company career pages for postings matching software engineering /
AI / full-stack roles, emails you only the new ones, and is meant to run
hourly via your OS scheduler.

## How it works

- Companies on **Greenhouse, Lever, SmartRecruiters, or Ashby** are hit via
  their public JSON APIs — fast, reliable, no HTML parsing.
- Everything else falls back to a **generic HTML scraper** that scans links
  on the career page for keyword matches.
  - Limitation: this only sees the initial HTML. Career pages that load
    listings via JavaScript (many React/Angular sites, e.g. some Workday
    setups) won't return results here. If a chunk of your list falls in
    this bucket, the next step is adding a Playwright-based renderer —
    ask and I'll add it.
- A local SQLite file (`jobs.db`) remembers every URL you've already been
  emailed about, so each run only reports genuinely new postings.

## Setup

1. **Install dependencies**
   ```
   cd job-scraper
   pip install -r requirements.txt
   ```

2. **Add your companies**
   Copy `config/companies.example.yaml` to `config/companies.yaml` and fill
   in your 100+ companies. For each one, figure out which platform its
   career page is on:
   - `boards.greenhouse.io/<company>` → `type: greenhouse`
   - `jobs.lever.co/<company>` → `type: lever`
   - `jobs.smartrecruiters.com/<company>` → `type: smartrecruiters`
   - `jobs.ashbyhq.com/<company>` → `type: ashby`
   - Anything else → `type: generic` (or just omit `type`, it auto-detects
     the first four)

3. **Set up email**
   Copy `.env.example` to `.env` and fill it in. If using Gmail:
   - Turn on 2-Step Verification on the account
   - Create an **App Password** (Google Account → Security → App passwords)
   - Use that 16-character password as `SMTP_PASS`, not your normal login
     password

4. **Test it**
   ```
   python main.py
   ```
   Check `scraper.log` for per-company results. First run will email you
   every current match (nothing's "seen" yet) — expect a big first email,
   then only deltas after that.

## Scheduling hourly

**Windows (Task Scheduler)**
- Task Scheduler → Create Task
- Trigger: Daily, repeat every 1 hour, for a duration of 24 hours (or
  "indefinitely")
- Action: Start a program
  - Program: path to `python.exe`
  - Arguments: `main.py`
  - Start in: the `job-scraper` folder (important — relative paths depend
    on this)

**macOS / Linux (cron)**
```
crontab -e
```
Add:
```
0 * * * * cd /full/path/to/job-scraper && /usr/bin/python3 main.py >> cron.log 2>&1
```

## Notes

- `REQUEST_DELAY_SECONDS` in `main.py` adds a 1s pause between companies —
  keep this to avoid hammering any single site.
- Some sites' terms of service restrict automated access — this is fine for
  personal, low-frequency checking of public postings, but avoid cranking
  the frequency up much further or removing the delay.
