"""
DriveFlow content agent — picks the next planned row from content-plan.csv,
writes HTML using Claude + site-knowledge.md, saves to guides/ per published_url.

Run from my-frontend-new (driveflow-frontend repo root):
  python _agent/generate_article.py

Requires: ANTHROPIC_API_KEY env var, pip install anthropic
"""

import anthropic
import csv
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
SITE_ROOT = AGENT_DIR.parent
KNOWLEDGE_FILE = AGENT_DIR / "site-knowledge.md"
CONTENT_PLAN = AGENT_DIR / "content-plan.csv"
GUIDES_DIR = SITE_ROOT / "guides"
SITEMAP_PATH = SITE_ROOT / "sitemap.xml"
GUIDES_INDEX_PATH = SITE_ROOT / "guides-index.json"
SITE_ORIGIN = "https://www.driveflow.ie"
DEFAULT_OG_IMAGE = f"{SITE_ORIGIN}/favicon.png"
GUIDE_SITEMAP_PRIORITY = "0.8"

GOOGLE_ADS_TAG = """<!-- Google tag (gtag.js) - Ads -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-17936809057"></script>
<script>
  gtag('config', 'AW-17936809057');
</script>"""

# All SEO guide types in the current content plan (not route-content / site-page).
AUTOMATABLE_TYPES = {
    "guide",
    "article",
    "fail-spots",
    "pass-guide",
    "roundabouts",
    "checklist",
    "comparison",
    "city-guide",
    "centre-guide",
    "route-guide",
    "manoeuvre",
    "junctions",
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")

# Injected into every generation prompt
STYLE_RULES = """
**Mandatory style rules:**
- Never use the em dash character (—). Do not use dashes to join two sentences. Use commas, periods, or parentheses instead.
- Always write **practice** and **practicing**. Never use practise or practising.
"""

TYPE_INSTRUCTIONS = {
    "fail-spots": """
**Article type: fail-spots**
- Structure as a clear "Top 10" (or similar numbered) list of specific fail locations and mistakes.
- Name real road types, junctions, roundabouts, or areas typical for this test centre (use careful wording: "commonly reported", "learners often fail here").
- Each item: what goes wrong + how to avoid it.
- Strong internal link to the target centre's route page and /routes.html.
""",
    "pass-guide": """
**Article type: pass-guide**
- Practical "how to pass" guide for the named test centre.
- Cover preparation, what examiners focus on, common local challenges, and test-day mindset.
- Include a clear CTA to practice routes on DriveFlow (link the centre's `-routes.html` page).
- Do not guarantee a pass.
""",
    "roundabouts": """
**Article type: roundabouts**
- Focus on Dublin driving tests (multiple centres: Tallaght, Finglas, Raheny, Dun Laoghaire, Naas, etc.).
- Explain approach, lane choice, observation, signalling, and common marks lost.
- Link to relevant Dublin-area centre route pages from the internal link map.
""",
    "checklist": """
**Article type: checklist**
- Use a scannable checklist format (before test day, day of test, during test).
- Mention 2026 where appropriate for the title/intro (Irish RSA context).
- Link to /routes.html and relevant preparation guides.
""",
    "comparison": """
**Article type: comparison**
- Compare Irish test centres (hardest / easiest) using pass-rate context carefully. Avoid false precision; cite that rates vary by year and source.
- Help learners choose preparation strategy, not just "pick the easy centre".
- Link to multiple centre route pages and /routes.html.
""",
    "city-guide": """
**Article type: city-guide**
- Hub-style guide for driving tests in that city (Dublin, Cork, or Galway).
- List major test centres in the area with short descriptions and internal links to each `-routes.html` page.
- Explain why local route practice matters in that city.
""",
    "centre-guide": """
**Article type: centre-guide**
- Complete local guide for one named RSA test centre: roads, areas, junctions, and what to expect.
- Cover typical route corridors, pressure points, and how to prepare in that specific area.
- Strong CTA and internal links to that centre's `-routes.html` page and /routes.html.
- Do not invent exact official RSA route maps; use careful wording (commonly reported / typical areas).
""",
    "route-guide": """
**Article type: route-guide**
- National or educational guide about practicing RSA driving test routes (why, how, how often, finding local routes).
- Emphasize local test-area practice and DriveFlow as the way to open centre routes in Google Maps.
- Link heavily to /routes.html and relevant centre `-routes.html` pages where natural.
- Strong commercial/route-intent focus without hard-sell hype.
""",
    "manoeuvre": """
**Article type: manoeuvre**
- Focus on one practical test manoeuvre for the named centre (e.g. reverse around the corner, hill start).
- Explain where learners commonly practice or encounter it, what examiners watch for, and how to avoid faults.
- Link to the centre's `-routes.html` page and related fail-spot or pass guides if relevant.
""",
    "junctions": """
**Article type: junctions**
- Focus on difficult junctions and roundabouts for the named test centre.
- Cover approach, lane choice, observation, signalling, and common marks lost at specific local pressure points.
- Link to the centre's `-routes.html` page and /routes.html.
""",
    "guide": """
**Article type: guide**
- General educational article; thorough, SEO-friendly, learner-focused.
- Link to relevant centre pages and /routes.html where natural.
""",
    "article": """
**Article type: article**
- Same as guide: educational SEO content for Irish learner drivers.
""",
}


def pick_next_topic(plan_path: Path) -> tuple[int, dict] | None:
    """Highest-priority first planned row with an automatable type."""
    with open(plan_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    candidates: list[tuple[int, dict]] = []
    for i, row in enumerate(rows):
        status = row.get("status", "").strip().lower()
        row_type = row.get("type", "").strip().lower()
        if status == "planned" and row_type in AUTOMATABLE_TYPES:
            candidates.append((i, row))

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(item[1].get("priority", "").strip().lower(), 99),
            item[0],
        )
    )
    i, row = candidates[0]
    return i, row


def update_plan(plan_path: Path, row_index: int, published_url: str):
    with open(plan_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    rows[row_index]["status"] = "done"
    rows[row_index]["published_url"] = published_url

    with open(plan_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def normalize_published_url(row: dict) -> str:
    """Use published_url from CSV when set; otherwise derive from topic."""
    url = (row.get("published_url") or "").strip()
    if url:
        return url if url.startswith("/") else f"/{url}"
    return f"/guides/{slugify(row['topic'])}.html"


def published_url_to_output_path(published_url: str) -> Path:
    """Map /guides/foo.html → SITE_ROOT/guides/foo.html"""
    rel = published_url.lstrip("/")
    return SITE_ROOT / rel


def centre_route_hint(centre: str) -> str:
    """Rough hint for prompt; model should still use link map."""
    overrides = {
        "Dun Laoghaire": "/dun-laoghaire-routes.html",
        "Carlow – Talbot Hotel": "/carlow-talbot-hotel-routes.html",
        "Birr – County Arms Hotel": "/birr-county-arms-hotel-routes.html",
        "Kilkenny – O'Loughlin Gaels": "/kilkenny-oloughlin-gaels-routes.html",
        "Kilkenny – Government Buildings": "/kilkenny-government-buildings-routes.html",
        "Limerick – Castlemungret": "/limerick-castlemungret-routes.html",
        "Newcastle West – Longcourt House Hotel": "/newcastle-west-longcourt-house-hotel-routes.html",
        "Westside": "/westside-routes.html",
        "Clybaun": "/clybaun-routes.html",
        "Maple House": "/maple-house-routes.html",
    }
    if centre in overrides:
        return overrides[centre]
    return f"/{slugify(centre)}-routes.html"


def build_prompt(knowledge: str, row: dict, published_url: str) -> str:
    topic = row.get("topic", "").strip()
    article_type = row.get("type", "guide").strip().lower()
    target_centre = row.get("target_centre", "").strip()
    priority = row.get("priority", "").strip()
    notes = row.get("notes", "").strip()

    type_block = TYPE_INSTRUCTIONS.get(article_type, TYPE_INSTRUCTIONS["guide"])

    if target_centre:
        route_hint = centre_route_hint(target_centre)
        centre_line = (
            f"Target test centre: **{target_centre}**. "
            f"Primary internal link: **{route_hint}** (verify against the internal link map)."
        )
    elif article_type == "city-guide" and topic:
        centre_line = (
            f"City hub article: link every major test centre in that city from the internal link map."
        )
    else:
        centre_line = "Not limited to a single test centre. Link several relevant centres from the internal link map."

    notes_line = f"\n**Editor notes:** {notes}" if notes else ""
    canonical = f"https://www.driveflow.ie{published_url}"

    return f"""You are a content writer for driveflow.ie, an Irish driving test prep website.

## Site Knowledge Base
{knowledge}

## Article Brief
- **Topic:** {topic}
- **Type:** {article_type}
- **Priority:** {priority}
- {centre_line}
- **Required published URL:** {published_url}
- **Required canonical URL:** {canonical}
- **Today's date:** {date.today().isoformat()}
{notes_line}

{type_block}

{STYLE_RULES}

## Task
Write a complete, publication-ready HTML guide for driveflow.ie.

Requirements:
1. Match the tone, structure, and HTML conventions in the Site Knowledge Base exactly.
2. Use the **guide article** HTML template from the Site Knowledge Base (guides/why-learners-fail-driving-test-ireland/index.html pattern): inline DriveFlow CSS variables, <main> + article card.
3. Set `<link rel="canonical">` and any og:url to **{canonical}** exactly.
4. Aim for 700–1000 words unless the article type is a checklist (can be structured with shorter items).
5. Include relevant internal links from the internal link map (paths like /raheny-routes.html, not /test-centres/raheny).
6. Link the RSA to https://www.rsa.ie when mentioned.
7. Do NOT include prices, phone numbers, or named instructor recommendations.
8. Do NOT use em dashes (—). Do NOT use practise or practising; use practice and practicing only.
9. Output ONLY the raw HTML: no markdown fences, no explanation, nothing before <!DOCTYPE or after </html>.
10. Include full SEO in <head> (see Site Knowledge Base "Guide SEO head" section): robots, favicons, Open Graph, Twitter Card, Article JSON-LD, Google Ads tag.
"""


def _extract_meta_content(html: str, name: str) -> str | None:
    pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"'
    m = re.search(pattern, html, re.I)
    return m.group(1).strip() if m else None


def _extract_og_content(html: str, prop: str) -> str | None:
    pattern = rf'<meta\s+property="og:{re.escape(prop)}"\s+content="([^"]*)"'
    m = re.search(pattern, html, re.I)
    return m.group(1).strip() if m else None


def _extract_title_text(html: str) -> str | None:
    m = re.search(r"<title>([^<]*)</title>", html, re.I)
    if not m:
        return None
    title = m.group(1).strip()
    title = re.sub(r"\s*\|\s*DriveFlow\s*$", "", title, flags=re.I)
    return title or None


def _extract_h1_text(html: str) -> str | None:
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.I)
    return m.group(1).strip() if m else None


def _html_contains(html: str, fragment: str) -> bool:
    return fragment.lower() in html.lower()


def _insert_after_head_open(html: str, block: str) -> str:
    m = re.search(r"(<head[^>]*>)", html, re.I)
    if m:
        pos = m.end()
        return html[:pos] + "\n" + block + html[pos:]
    return block + "\n" + html


def _insert_before_style_or_body(html: str, block: str) -> str:
    for marker in ("<style", "<main", "<body"):
        m = re.search(marker, html, re.I)
        if m:
            return html[: m.start()] + block + "\n" + html[m.start() :]
    return html.replace("</head>", block + "\n</head>", 1)


def build_article_json_ld(
    headline: str, description: str, canonical: str, published_url: str
) -> str:
    today = date.today().isoformat()
    safe_headline = headline.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{safe_headline}",
  "description": "{safe_desc}",
  "url": "{canonical}",
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "{canonical}"
  }},
  "image": "{DEFAULT_OG_IMAGE}",
  "author": {{
    "@type": "Organization",
    "name": "DriveFlow",
    "url": "{SITE_ORIGIN}/"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "DriveFlow",
    "logo": {{
      "@type": "ImageObject",
      "url": "{DEFAULT_OG_IMAGE}"
    }}
  }},
  "datePublished": "{today}",
  "dateModified": "{today}",
  "inLanguage": "en-IE"
}}
</script>"""


def ensure_seo_tags(html: str, published_url: str, topic: str) -> str:
    """Ensure guides have the same indexing tags as route pages (deterministic post-process)."""
    canonical = f"{SITE_ORIGIN}{published_url}"
    description = (
        _extract_meta_content(html, "description")
        or _extract_og_content(html, "description")
        or f"Practical Irish driving test advice: {topic}. Learner-focused tips from DriveFlow."
    )
    headline = (
        _extract_title_text(html)
        or _extract_og_content(html, "title")
        or _extract_h1_text(html)
        or topic
    )
    og_title = _extract_og_content(html, "title") or headline

    tags: list[str] = []

    if not _html_contains(html, 'name="robots"'):
        tags.append('<meta name="robots" content="index, follow, max-image-preview:large">')

    favicon_tags = [
        ('rel="icon" href="https://www.driveflow.ie/favicon.ico"', '<link rel="icon" href="https://www.driveflow.ie/favicon.ico">'),
        ('sizes="32x32"', '<link rel="icon" type="image/png" sizes="32x32" href="https://www.driveflow.ie/favicon.png">'),
        ('sizes="192x192"', '<link rel="icon" type="image/png" sizes="192x192" href="https://www.driveflow.ie/favicon.png">'),
        ('apple-touch-icon"', '<link rel="apple-touch-icon" href="https://www.driveflow.ie/favicon.png">'),
    ]
    for needle, tag in favicon_tags:
        if not _html_contains(html, needle):
            tags.append(tag)

    if not _html_contains(html, 'rel="canonical"'):
        tags.append(f'<link rel="canonical" href="{canonical}">')
    else:
        html = re.sub(
            r'<link\s+rel="canonical"\s+href="[^"]*"',
            f'<link rel="canonical" href="{canonical}"',
            html,
            count=1,
            flags=re.I,
        )

    og_pairs = [
        ("og:title", og_title),
        ("og:description", description),
        ("og:url", canonical),
        ("og:type", "article"),
        ("og:image", DEFAULT_OG_IMAGE),
        ("og:site_name", "DriveFlow"),
        ("og:locale", "en_IE"),
    ]
    for prop, value in og_pairs:
        if not _html_contains(html, f'property="{prop}"'):
            esc = value.replace('"', "&quot;")
            tags.append(f'<meta property="{prop}" content="{esc}">')

    twitter_pairs = [
        ("twitter:card", "summary_large_image"),
        ("twitter:title", og_title),
        ("twitter:description", description),
        ("twitter:url", canonical),
        ("twitter:image", DEFAULT_OG_IMAGE),
    ]
    for name, value in twitter_pairs:
        if not _html_contains(html, f'name="{name}"'):
            esc = value.replace('"', "&quot;")
            tags.append(f'<meta name="{name}" content="{esc}">')

    if tags:
        block = "\n".join(tags) + "\n"
        if _html_contains(html, "charset"):
            html = re.sub(
                r'(<meta\s+charset[^>]*>\s*)',
                r"\1" + block,
                html,
                count=1,
                flags=re.I,
            )
        else:
            html = _insert_after_head_open(html, block)

    if "AW-17936809057" not in html:
        if _html_contains(html, "G-EJB69589QP"):
            html = re.sub(
                r"(</script>\s*)(?=<meta|<link|<title|<style)",
                r"\1\n" + GOOGLE_ADS_TAG + "\n",
                html,
                count=1,
                flags=re.I,
            )
        else:
            html = _insert_after_head_open(html, GOOGLE_ADS_TAG)

    json_ld = build_article_json_ld(headline, description, canonical, published_url)
    if '"@type": "Article"' not in html and '"@type":"Article"' not in html:
        html = _insert_before_style_or_body(html, json_ld)

    return html


def add_to_sitemap(published_url: str) -> bool:
    """Append guide URL to sitemap.xml if not already listed. Returns True if added.

    Dedupes by exact <loc> match to avoid reintroducing duplicate URLs.
    """
    if not SITEMAP_PATH.exists():
        print(f"WARNING: {SITEMAP_PATH} not found; skipping sitemap update.")
        return False

    loc = f"{SITE_ORIGIN}{published_url}"
    content = SITEMAP_PATH.read_text(encoding="utf-8")
    # Exact <loc> match only (avoids false positives from substring overlaps)
    if f"<loc>{loc}</loc>" in content:
        print(f"Sitemap already contains: {loc}")
        return False

    lastmod = date.today().isoformat()
    entry = f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{GUIDE_SITEMAP_PRIORITY}</priority>
  </url>
"""
    if "</urlset>" not in content:
        print("WARNING: sitemap.xml has no </urlset>; skipping sitemap update.")
        return False

    content = content.replace("</urlset>", entry + "</urlset>", 1)
    SITEMAP_PATH.write_text(content, encoding="utf-8")
    print(f"Sitemap updated: {loc}")
    return True


def update_guides_index(
    published_url: str, title: str, description: str
) -> bool:
    """Add or update an entry in guides-index.json for the guides hub page."""
    entry = {
        "title": title,
        "url": published_url,
        "description": description[:200] if description else "",
    }

    guides: list[dict] = []
    if GUIDES_INDEX_PATH.exists():
        try:
            guides = json.loads(GUIDES_INDEX_PATH.read_text(encoding="utf-8"))
            if not isinstance(guides, list):
                guides = []
        except json.JSONDecodeError:
            guides = []

    updated = False
    for i, g in enumerate(guides):
        if g.get("url") == published_url:
            guides[i] = entry
            updated = True
            break

    if not updated:
        guides.append(entry)

    GUIDES_INDEX_PATH.write_text(
        json.dumps(guides, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Guides index updated: {published_url}")
    return True


def main():
    for path in [KNOWLEDGE_FILE, CONTENT_PLAN]:
        if not path.exists():
            print(f"ERROR: {path} not found.")
            sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    result = pick_next_topic(CONTENT_PLAN)
    if result is None:
        print(
            "No planned topics in content-plan.csv. "
            f"Supported types: {', '.join(sorted(AUTOMATABLE_TYPES))}"
        )
        sys.exit(0)

    row_index, row = result
    published_url = normalize_published_url(row)
    output_path = published_url_to_output_path(published_url)

    print(f"Generating: [{row.get('type')}] {row['topic']}")
    print(f"Output: {output_path.relative_to(SITE_ROOT)}")
    print(f"URL: {published_url}")

    knowledge = KNOWLEDGE_FILE.read_text(encoding="utf-8")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": build_prompt(knowledge, row, published_url)}],
    )
    html_content = message.content[0].text.strip()

    if html_content.startswith("```"):
        html_content = re.sub(r"^```(?:html)?\s*", "", html_content)
        html_content = re.sub(r"\s*```$", "", html_content)

    # Safety net: strip em dashes only (do not rewrite "practise" inside URL paths)
    html_content = html_content.replace("—", ", ")

    html_content = ensure_seo_tags(html_content, published_url, row.get("topic", "").strip())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Saved: {output_path}")

    add_to_sitemap(published_url)

    index_title = _extract_title_text(html_content) or row.get("topic", "").strip()
    index_description = (
        _extract_meta_content(html_content, "description")
        or f"Practical Irish driving test advice: {row.get('topic', '').strip()}."
    )
    update_guides_index(published_url, index_title, index_description)

    update_plan(CONTENT_PLAN, row_index, published_url)
    print(f"Content plan updated — status=done, published_url={published_url}")


if __name__ == "__main__":
    main()
