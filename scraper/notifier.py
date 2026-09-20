import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_digest(new_postings):
    if not new_postings:
        return

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    to_addr = os.environ.get("NOTIFY_TO", smtp_user)

    by_company = {}
    for p in new_postings:
        by_company.setdefault(p["company"], []).append(p)

    lines = []
    for company, jobs in by_company.items():
        lines.append(f"== {company} ==")
        for j in jobs:
            note = j.get("yoe_note")
            suffix = f" ({note})" if note else ""
            lines.append(f"- {j['title']}{suffix}\n  {j['url']}")
        lines.append("")
    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["Subject"] = f"[Job Scraper] {len(new_postings)} new matching posting(s)"
    msg["From"] = smtp_user
    msg["To"] = to_addr
    # Explicit utf-8: scraped titles/descriptions routinely contain non-ASCII
    # characters (non-breaking spaces, smart quotes, accents). Plain
    # MIMEText(body, "plain") defaults to us-ascii and crashes on send —
    # that's what threw the 'ascii' codec error.
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_addr], msg.as_string())
