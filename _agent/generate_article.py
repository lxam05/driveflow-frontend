"""
DriveFlow content agent — picks the next planned row from content-plan.csv,
writes HTML using Claude + site-knowledge.md, saves to guides/ per published_url.

Run from my-frontend-new (driveflow-frontend repo root):
  python _agent/generate_article.py

Requires: ANTHROPIC_API_KEY env var, pip install anthropic
"""

import anthropic
import csv
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
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")

TYPE_INSTRUCTIONS = {
    "fail-spots": """
**Article type: fail-spots**
- Structure as a clear "Top 10" (or similar numbered) list of specific fail locations and mistakes.
- Name real road types, junctions, roundabouts, or areas typical for this test centre (use careful wording — "commonly reported", "learners often fail here").
- Each item: what goes wrong + how to avoid it.
- Strong internal link to the target centre's route page and /routes.html.
""",
    "pass-guide": """
**Article type: pass-guide**
- Practical "how to pass" guide for the named test centre.
- Cover preparation, what examiners focus on, common local challenges, and test-day mindset.
- Include a clear CTA to practise routes on DriveFlow (link the centre's `-routes.html` page).
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
- Compare Irish test centres (hardest / easiest) using pass-rate context carefully — avoid false precision; cite that rates vary by year and source.
- Help learners choose preparation strategy, not just "pick the easy centre".
- Link to multiple centre route pages and /routes.html.
""",
    "city-guide": """
**Article type: city-guide**
- Hub-style guide for driving tests in that city (Dublin, Cork, or Galway).
- List major test centres in the area with short descriptions and internal links to each `-routes.html` page.
- Explain why local route practice matters in that city.
""",
    "guide": """
**Article type: guide**
- General educational article; thorough, SEO-friendly, learner-focused.
- Link to relevant centre pages and /routes.html where natural.
""",
    "article": """
**Article type: article**
- Same as guide — educational SEO content for Irish learner drivers.
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
            f"City hub article — link every major test centre in that city from the internal link map."
        )
    else:
        centre_line = "Not limited to a single test centre — link several relevant centres from the internal link map."

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

## Task
Write a complete, publication-ready HTML guide for driveflow.ie.

Requirements:
1. Match the tone, structure, and HTML conventions in the Site Knowledge Base exactly.
2. Use the **guide article** HTML template from the Site Knowledge Base (guides/why-learners-fail-driving-test-ireland/index.html pattern) — inline DriveFlow CSS variables, <main> + article card.
3. Set `<link rel="canonical">` and any og:url to **{canonical}** exactly.
4. Aim for 700–1000 words unless the article type is a checklist (can be structured with shorter items).
5. Include relevant internal links from the internal link map (paths like /raheny-routes.html, not /test-centres/raheny).
6. Link the RSA to https://www.rsa.ie when mentioned.
7. Do NOT include prices, phone numbers, or named instructor recommendations.
8. Output ONLY the raw HTML — no markdown fences, no explanation, nothing before <!DOCTYPE or after </html>.
"""


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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Saved: {output_path}")

    update_plan(CONTENT_PLAN, row_index, published_url)
    print(f"Content plan updated — status=done, published_url={published_url}")


if __name__ == "__main__":
    main()
