"""
ACR129 Lagos-California Blog Auto-Publisher
Get Help Rural-Urban Foundation
Runs every Tuesday & Friday at 5pm WAT (4pm UTC) via GitHub Actions.
Searches for Lagos-California Sister-State ACR129 news and publishes
a new blog post to the NGO website (index.html).
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import sys
import json
import hashlib

# ── Nigerian time (WAT = UTC+1) ──────────────────────────────────────────────
WAT = timezone(timedelta(hours=1))
NOW = datetime.now(WAT)
DATE_STR   = NOW.strftime("%B %d, %Y")          # e.g. June 18, 2026
DATE_SHORT = NOW.strftime("%Y-%m-%d")           # e.g. 2026-06-18
POST_ID    = f"acr129-{DATE_SHORT.replace('-', '')}"  # e.g. acr129-20260618

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
    """Return list of (title, url) tuples matching ACR129 keywords."""
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
        print(f"  → {len(items)} result(s)")
        all_items.extend(items)
    return all_items


def build_post_html(headlines):
    """Build the HTML content for a new blog post."""
    if headlines:
        # Build a proper news digest with real headlines
        news_list_items = ""
        sources_used = set()
        for h in headlines[:6]:
            sources_used.add(h["source"])
            news_list_items += f"""
            <li>
              <strong>{h['title']}</strong><br>
              <em>Source: {h['source']}</em> —
              <a href="{h['url']}" target="_blank" rel="noopener">Read full article →</a>
            </li>"""

        news_section = f"""
          <h3>Latest News & Developments</h3>
          <ul>{news_list_items}
          </ul>"""
        summary_note = (
            f"This week's update draws from {len(sources_used)} source(s): "
            + ", ".join(sources_used) + "."
        )
    else:
        # No new headlines found — publish a programme awareness post
        news_section = """
          <h3>Programme Overview</h3>
          <p>
            ACR129 — California Assembly Concurrent Resolution 129 — formally recognises
            the Sister-State relationship between Lagos, Nigeria and California, USA.
            This landmark resolution, championed by Assemblymember Matt Haney, opens
            doors for cultural exchange, trade, diaspora development, and joint
            investment initiatives between the two dynamic regions.
          </p>"""
        summary_note = (
            "No new breaking headlines found this cycle; this post covers the "
            "programme background and ongoing benefits."
        )

    html_content = f"""
        <p>
          The <strong>Lagos–California ACR129 Sister-State Partnership</strong> continues
          to advance opportunities that directly benefit Nigerian communities at home and
          in the diaspora. Get Help Rural-Urban Foundation is actively monitoring this
          programme because of its potential to unlock resources, mentorship, and
          investment for the rural and urban communities we serve — particularly in
          Cross River State and Lagos State.
        </p>
        {news_section}
        <h3>Key Benefits for Nigerian Communities</h3>
        <ul>
          <li><strong>Economic Growth:</strong> ACR129 promotes trade partnerships between
            Lagos-based businesses and California companies, creating opportunities
            for small enterprises and cooperatives in rural areas.</li>
          <li><strong>Educational Exchange:</strong> Students and professionals gain
            access to exchange programmes, scholarships, and technical training
            opportunities with Californian institutions.</li>
          <li><strong>Diaspora Engagement:</strong> Nigerians in California are
            empowered to invest back home through structured diaspora remittance
            and development channels supported under the resolution.</li>
          <li><strong>Healthcare & Social Development:</strong> The partnership
            encourages knowledge transfer in public health, sanitation, and
            community development — areas central to our foundation's work.</li>
          <li><strong>Cultural Diplomacy:</strong> People-to-people ties are
            strengthened through arts, culture, and civic exchange programmes,
            fostering goodwill and international visibility for Lagos and Nigeria.</li>
        </ul>
        <h3>How Get Help Rural-Urban Foundation Is Engaged</h3>
        <p>
          Our foundation is monitoring the ACR129 programme closely as part of our
          mandate to connect underserved communities with global opportunities.
          We encourage our volunteers, partners, and community members to stay informed
          and reach out to us at
          <a href="mailto:support.ru.ngo@gmail.com">support.ru.ngo@gmail.com</a>
          if they have ideas for how our foundation can collaborate within this
          Lagos–California framework.
        </p>
        <p><em>{summary_note}</em></p>"""

    return html_content


def build_post_js_entry(post_id, title, html_content):
    """Return the JS object entry string for this post."""
    # Escape single quotes and backticks in html_content for JS template literal
    safe_content = html_content.replace('`', '\\`').replace('${', '\\${')
    safe_title   = title.replace("'", "\\'")
    category     = "News"
    excerpt      = (
        "The Lagos–California ACR129 Sister-State Partnership continues to advance "
        "opportunities for Nigerian communities. Read our latest update and analysis."
    )
    safe_excerpt = excerpt.replace("'", "\\'")

    entry = f"""  '{post_id}': {{
    title:    '{safe_title}',
    date:     '{DATE_STR}',
    author:   'Get Help Rural-Urban Foundation',
    category: '{category}',
    excerpt:  '{safe_excerpt}',
    content:  `{safe_content}`
  }},"""
    return entry


def inject_post_into_index(post_id, post_js_entry, post_card_html):
    """Read index.html, inject the new post, write it back."""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # ── 1. Check if this post already exists (idempotent) ─────────────────
    if post_id in html:
        print(f"Post '{post_id}' already exists in index.html — skipping.")
        return False

    # ── 2. Inject into the posts JS object ────────────────────────────────
    # Use plain string search to avoid regex backslash issues
    marker = "const posts = {"
    pos = html.find(marker)
    if pos == -1:
        print("ERROR: Could not find 'const posts = {' in index.html", file=sys.stderr)
        return False
    insert_at = pos + len(marker)
    html = html[:insert_at] + "\n" + post_js_entry + html[insert_at:]

    # ── 3. Inject post card into the blog grid ────────────────────────────
    # Find id="blog-latest" and insert card after the closing > of its tag
    grid_marker = 'id="blog-latest"'
    grid_pos = html.find(grid_marker)
    if grid_pos != -1:
        tag_end = html.find('>', grid_pos)
        if tag_end != -1:
            html = html[:tag_end+1] + "\n" + post_card_html + html[tag_end+1:]
        else:
            print("WARN: Could not find end of blog-latest tag", file=sys.stderr)
    else:
        # Fallback: prepend before the first post card
        first_card = html.find('<article class="post-card"')
        if first_card != -1:
            html = html[:first_card] + post_card_html + "\n" + html[first_card:]
        else:
            print("WARN: Could not find blog grid to inject card", file=sys.stderr)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Successfully injected post '{post_id}' into index.html")
    return True


def build_post_card_html(post_id, title):
    category_badge = '<span class="badge news">News</span>'
    excerpt = (
        "The Lagos–California ACR129 Sister-State Partnership continues to advance "
        "opportunities for Nigerian communities. Click to read our latest update."
    )
    return f"""              <article class="post-card" data-category="news" data-id="{post_id}" onclick="openPost('{post_id}')">
                <div class="post-img" style="background:var(--green-dark);display:flex;align-items:center;justify-content:center;">
                  <span style="font-size:2.5rem;">🌍</span>
                </div>
                <div class="post-body">
                  {category_badge}
                  <h3>{title}</h3>
                  <p class="post-meta">{DATE_STR} · Get Help Rural-Urban Foundation</p>
                  <p>{excerpt}</p>
                  <button class="btn-link" onclick="openPost('{post_id}');event.stopPropagation()">Read More →</button>
                </div>
              </article>"""


def main():
    print(f"\n=== ACR129 Blog Publisher | {DATE_STR} ===\n")

    headlines = collect_all_headlines()
    print(f"\nTotal relevant headlines found: {len(headlines)}")

    title         = f"Lagos–California ACR129 Update: {DATE_STR}"
    html_content  = build_post_html(headlines)
    post_js_entry = build_post_js_entry(POST_ID, title, html_content)
    post_card     = build_post_card_html(POST_ID, title)

    injected = inject_post_into_index(POST_ID, post_js_entry, post_card)

    if injected:
        print(f"\n✅ New post '{POST_ID}' added to website successfully.")
    else:
        print(f"\n⏭  No changes made.")

    sys.exit(0)


if __name__ == "__main__":
    main()
