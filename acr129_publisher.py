"""
ACR129 Lagos-California News Collector
Get Help Rural-Urban Foundation
Runs every Tuesday & Friday at 5pm WAT (4pm UTC) via GitHub Actions.
Searches for Lagos-California Sister-State ACR129 news and emails a digest
to support.ru.ngo@gmail.com for manual review before blog publishing.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ── Nigerian time (WAT = UTC+1) ──────────────────────────────────────────────
WAT      = timezone(timedelta(hours=1))
NOW      = datetime.now(WAT)
DATE_STR = NOW.strftime("%B %d, %Y")   # e.g. July 22, 2026

# ── Email config ─────────────────────────────────────────────────────────────
GMAIL_USER     = "support.ru.ngo@gmail.com"
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
EMAIL_TO       = "support.ru.ngo@gmail.com"

# ── News sources ─────────────────────────────────────────────────────────────
SOURCES = [
    {
        "name": "Lagos Diaspora Commission",
        "url": "https://lagosdiaspora.ng",
        "search_url": "https://lagosdiaspora.ng/?s=ACR129+California",
        "selector": "article h2 a, .entry-title a, h2.post-title a",
    },
    {
        "name": "Assemblymember Haney's Office",
        "url": "https://haney.asmdc.org",
        "search_url": "https://haney.asmdc.org/?s=Lagos",
        "selector": "article h2 a, .entry-title a, h2 a",
    },
    {
        "name": "PM News Nigeria",
        "url": "https://pmnewsnigeria.com",
        "search_url": "https://pmnewsnigeria.com/?s=ACR129+Lagos+California",
        "selector": "article h2 a, .entry-title a, h3.title a",
    },
    {
        "name": "Lagos Foreign Relations",
        "url": "https://foreignrelations.lagosstate.gov.ng",
        "search_url": "https://foreignrelations.lagosstate.gov.ng/?s=California",
        "selector": "article h2 a, .entry-title a",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GetHelpRuralUrban-NewsBot/1.0)"
}
KEYWORDS = [
    "ACR129", "ACR 129", "Lagos", "California", "sister state",
    "diaspora", "partnership", "bilateral", "cooperation",
    "haney", "lagos-california"
]


def fetch_headlines(source):
    """Return list of dicts with title, url, source matching ACR129 keywords."""
    found = []
    try:
        resp = requests.get(source["search_url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select(source["selector"])
        for link in links[:10]:
            title = link.get_text(strip=True)
            href  = link.get("href", "")
            if not title or not href:
                continue
            title_lower = title.lower() + " " + href.lower()
            if any(kw.lower() in title_lower for kw in KEYWORDS):
                found.append({"title": title, "url": href, "source": source["name"]})
    except Exception as e:
        print(f"  [WARN] Could not fetch {source['name']}: {e}", file=sys.stderr)
    return found


def collect_all_headlines():
    all_items = []
    for src in SOURCES:
        print(f"Checking {src['name']}...")
        items = fetch_headlines(src)
        print(f"  -> {len(items)} result(s)")
        all_items.extend(items)
    return all_items


def send_email(headlines):
    if not GMAIL_PASSWORD:
        print("ERROR: GMAIL_APP_PASSWORD secret is not set in GitHub secrets.", file=sys.stderr)
        sys.exit(1)

    subject = f"ACR129 News Digest for Review — {DATE_STR}"

    if headlines:
        rows = ""
        for h in headlines:
            rows += f"""
        <tr>
          <td style="padding:8px;border:1px solid #ddd;"><strong>{h['title']}</strong></td>
          <td style="padding:8px;border:1px solid #ddd;">{h['source']}</td>
          <td style="padding:8px;border:1px solid #ddd;">
            <a href="{h['url']}" style="color:#1a7a3c;">Read article</a>
          </td>
        </tr>"""

        body_html = f"""
<html><body style="font-family:Arial,sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="background:#1a7a3c;padding:20px;border-radius:6px 6px 0 0;">
    <h2 style="color:#fff;margin:0;">ACR129 News Digest</h2>
    <p style="color:#d4edda;margin:4px 0 0;">{DATE_STR} &mdash; Get Help Rural-Urban Foundation</p>
  </div>
  <div style="padding:20px;border:1px solid #ddd;border-top:none;border-radius:0 0 6px 6px;">
    <p><strong>{len(headlines)} headline(s) found</strong> across news sources this cycle:</p>
    <table style="width:100%;border-collapse:collapse;margin-top:10px;">
      <tr style="background:#f5f5f5;">
        <th style="padding:8px;border:1px solid #ddd;text-align:left;">Headline</th>
        <th style="padding:8px;border:1px solid #ddd;text-align:left;">Source</th>
        <th style="padding:8px;border:1px solid #ddd;text-align:left;">Link</th>
      </tr>
      {rows}
    </table>
    <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">
    <p style="color:#555;">
      <strong>Next step:</strong> Forward this email to Claude (or paste the headlines)
      and say <em>"Turn these into a blog post and publish to the website."</em>
    </p>
  </div>
</body></html>"""

    else:
        body_html = f"""
<html><body style="font-family:Arial,sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="background:#1a7a3c;padding:20px;border-radius:6px 6px 0 0;">
    <h2 style="color:#fff;margin:0;">ACR129 News Digest</h2>
    <p style="color:#d4edda;margin:4px 0 0;">{DATE_STR} &mdash; Get Help Rural-Urban Foundation</p>
  </div>
  <div style="padding:20px;border:1px solid #ddd;border-top:none;border-radius:0 0 6px 6px;">
    <p><strong>No new headlines found</strong> this cycle across all four sources:</p>
    <ul>
      <li>Lagos Diaspora Commission</li>
      <li>Assemblymember Haney's Office</li>
      <li>PM News Nigeria</li>
      <li>Lagos Foreign Relations</li>
    </ul>
    <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">
    <p style="color:#555;">
      <strong>Next step:</strong> If you still want a blog post published this week,
      tell Claude <em>"Publish a programme overview post for ACR129 today."</em>
    </p>
  </div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, EMAIL_TO, msg.as_string())
        print(f"Email digest sent to {EMAIL_TO}")
    except Exception as e:
        print(f"ERROR sending email: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    print(f"\n=== ACR129 News Collector | {DATE_STR} ===\n")
    headlines = collect_all_headlines()
    print(f"\nTotal relevant headlines found: {len(headlines)}")
    send_email(headlines)
    print("\nDone.")
    sys.exit(0)


if __name__ == "__main__":
    main()
