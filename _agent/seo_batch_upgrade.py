#!/usr/bin/env python3
"""
One-off DriveFlow SEO batch upgrade for *-routes.html pages.

Writes static HTML improvements (head, schema, breadcrumbs, landmarks,
nearby links, FAQ schema where present, inlined txt bodies).
Does not touch premium route loading (#routes / data-route / shared.js auth).
"""
from __future__ import annotations

import html as html_lib
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PATH = Path(__file__).resolve().parent / "seo-centre-meta.json"
ORG_ID = "https://www.driveflow.ie/#organization"
WEB_ID = "https://www.driveflow.ie/#website"
OG_IMAGE = "https://www.driveflow.ie/backgroundForWeb.jpg"

GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-EJB69589QP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-EJB69589QP');
</script>
"""

HEAD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
{ga}<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<meta name="description" content="{description}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="https://www.driveflow.ie/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="https://www.driveflow.ie/favicon.png">
<link rel="icon" type="image/png" sizes="192x192" href="https://www.driveflow.ie/favicon.png">
<link rel="apple-touch-icon" href="https://www.driveflow.ie/favicon.png">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="DriveFlow">
<meta property="og:locale" content="en_IE">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<title>{title}</title>

<link rel="stylesheet" href="/shared.css">
{extra_head}</head>
"""


def esc(s: str) -> str:
    return html_lib.escape(s, quote=True)


def load_meta() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def extract_extra_head(html: str) -> str:
    """Preserve page-specific <style> blocks from original head."""
    m = re.search(r"<head[^>]*>(.*?)</head>", html, re.I | re.S)
    if not m:
        return ""
    head = m.group(1)
    styles = re.findall(r"<style\b[^>]*>.*?</style>", head, re.I | re.S)
    return "\n".join(styles) + ("\n" if styles else "")


def extract_body_inner(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.I | re.S)
    return m.group(1) if m else html


def strip_json_ld(html: str) -> str:
    return re.sub(
        r'<script\s+type=["\']application/ld\+json["\']\s*>.*?</script>\s*',
        "",
        html,
        flags=re.I | re.S,
    )


def strip_txt_fetch_scripts(html: str) -> tuple[str, str | None]:
    """Remove inline fetch(txt files/...) scripts; return txt path if found."""
    txt_path = None
    pattern = re.compile(
        r"<script>\s*\(function\s*\(\)\s*\{.*?fetch\(['\"]([^'\"]+\.txt)['\"].*?</script>",
        re.I | re.S,
    )

    def repl(m: re.Match) -> str:
        nonlocal txt_path
        txt_path = m.group(1)
        return ""

    cleaned = pattern.sub(repl, html)
    # Also catch simpler variants
    if txt_path is None:
        m2 = re.search(r"fetch\(['\"]([^'\"]+\.txt)['\"]", html)
        if m2:
            txt_path = m2.group(1)
            cleaned = re.sub(
                r"<script>\s*\(function\s*\(\)\s*\{.*?txt%20files.*?\}?\s*\)\(\);\s*</script>",
                "",
                cleaned,
                flags=re.I | re.S,
            )
            cleaned = re.sub(
                r"<script>\s*\(function\s*\(\)\s*\{.*?txt files.*?\}?\s*\)\(\);\s*</script>",
                "",
                cleaned,
                flags=re.I | re.S,
            )
    return cleaned, txt_path


def resolve_txt_path(encoded_or_path: str) -> Path | None:
    decoded = urllib.parse.unquote(encoded_or_path)
    # Paths like txt%20files/athlone.txt or txt files/athlone.txt
    candidate = ROOT / decoded
    if candidate.exists():
        return candidate
    # try relative variants
    name = Path(decoded).name
    alt = ROOT / "txt files" / name
    if alt.exists():
        return alt
    return None


def txt_to_html(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    parts = []
    for i, block in enumerate(blocks):
        cleaned = re.sub(r"\s+", " ", block).strip()
        if not cleaned:
            continue
        tag = "h2" if i == 0 else "p"
        parts.append(f"<{tag}>{esc(cleaned)}</{tag}>")
    return "\n".join(parts)


def extract_faqs_from_html(html: str) -> list[dict[str, str]]:
    """Extract FAQ Q/A from visible content (h4+p after FAQ heading, or existing FAQPage)."""
    faqs: list[dict[str, str]] = []

    # Prefer existing FAQPage JSON if present
    for m in re.finditer(
        r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            nodes = data["@graph"]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("@type") == "FAQPage":
                for ent in node.get("mainEntity") or []:
                    q = ent.get("name")
                    ans = (ent.get("acceptedAnswer") or {}).get("text")
                    if q and ans:
                        faqs.append({"question": q, "answer": ans})
        if faqs:
            return faqs

    # Visible: look for FAQ section with h4 questions
    faq_section = re.search(
        r"(?:FAQs?|Frequently Asked Questions)[^<]*</h[23]>(.*?)(?:<div\s+id=[\"']routes|</main>|id=[\"']sharedPurchase)",
        html,
        re.I | re.S,
    )
    search_html = faq_section.group(1) if faq_section else html
    pairs = re.findall(
        r"<h4[^>]*>(.*?)</h4>\s*<p[^>]*>(.*?)</p>",
        search_html,
        re.I | re.S,
    )
    for q, a in pairs:
        q_clean = re.sub(r"<[^>]+>", "", q).strip()
        a_clean = re.sub(r"<[^>]+>", "", a).strip()
        if "?" in q_clean and a_clean:
            faqs.append({"question": q_clean, "answer": a_clean})
    return faqs


def build_json_ld(meta: dict, faqs: list[dict[str, str]]) -> str:
    graph: list[dict] = [
        {
            "@type": "WebPage",
            "@id": meta["canonical"] + "#webpage",
            "url": meta["canonical"],
            "name": meta["title"],
            "description": meta["description"],
            "isPartOf": {"@id": WEB_ID},
            "about": {"@id": ORG_ID},
            "publisher": {"@id": ORG_ID},
            "inLanguage": "en-IE",
        },
        {
            "@type": "BreadcrumbList",
            "@id": meta["canonical"] + "#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": "https://www.driveflow.ie/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Driving Test Centres",
                    "item": "https://www.driveflow.ie/routes.html",
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": meta["displayName"],
                    "item": meta["canonical"],
                },
            ],
        },
    ]
    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": meta["canonical"] + "#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f["answer"],
                        },
                    }
                    for f in faqs
                ],
            }
        )
    payload = {"@context": "https://schema.org", "@graph": graph}
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + "\n</script>"
    )


def breadcrumb_html(meta: dict) -> str:
    return f"""<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol class="breadcrumb-list">
    <li><a href="/">Home</a></li>
    <li><a href="/routes.html">Driving Test Centres</a></li>
    <li aria-current="page">{esc(meta["displayName"])}</li>
  </ol>
</nav>
"""


def nearby_html(meta: dict, slug_to_name: dict[str, str]) -> str:
    nearby = meta.get("nearby") or []
    if not nearby:
        return ""
    items = []
    for slug in nearby:
        name = slug_to_name.get(slug, slug.replace("-", " ").title())
        items.append(
            f'      <li><a href="/{slug}-routes.html">{esc(name)} Driving Test Centre</a></li>'
        )
    return f"""<aside class="nearby-centres" aria-label="Nearby driving test centres">
  <h2>Nearby driving test centres</h2>
  <p>Also useful if you are practising around County {esc(meta["county"])}.</p>
  <ul>
{chr(10).join(items)}
  </ul>
</aside>
"""


def ensure_landmarks_and_chrome(
    body: str, meta: dict, slug_to_name: dict[str, str], inlined_info: str | None
) -> str:
    """Normalize structure: breadcrumbs, header, main, nearby, footer."""
    # Fix broken hub links
    body = body.replace("/driving-test-routes.html", "/routes.html")
    body = body.replace("driving-test-routes.html", "routes.html")

    # Remove existing breadcrumbs (we'll insert a canonical one)
    body = re.sub(
        r'<nav[^>]*class=["\'][^"\']*breadcrumb[^"\']*["\'][^>]*>.*?</nav>\s*',
        "",
        body,
        flags=re.I | re.S,
    )

    # Convert page-header div -> header (only when still a div; never re-close across siblings)
    if re.search(r'<div\s+class=["\']page-header["\']>', body, re.I):
        body = re.sub(
            r'<div\s+class=["\']page-header["\']>',
            '<header class="page-header">',
            body,
            count=1,
            flags=re.I,
        )
        m = re.search(
            r'(<header class="page-header">)(.*?)(</div>)(\s*(?:<div class="info-section"|<div id="routes"|<main|<aside|<!--))',
            body,
            re.I | re.S,
        )
        if m and "</header>" not in m.group(2):
            body = (
                body[: m.start()]
                + m.group(1)
                + m.group(2)
                + "</header>"
                + m.group(4)
                + body[m.end() :]
            )

    # Insert breadcrumb at start of container
    crumb = breadcrumb_html(meta)
    if 'class="container"' in body or "class='container'" in body:
        body = re.sub(
            r'(<div class="container">\s*)',
            r"\1" + crumb,
            body,
            count=1,
            flags=re.I,
        )
    else:
        body = crumb + body

    # Inline txt into empty info-section if needed
    if inlined_info:
        def fill_info(m: re.Match) -> str:
            inner = m.group(2).strip()
            if inner:
                return m.group(0)  # already has content
            return f'{m.group(1)}\n{inlined_info}\n</div>'

        body = re.sub(
            r'(<div\s+class=["\']info-section["\'][^>]*>)(.*?)(</div>)',
            fill_info,
            body,
            count=1,
            flags=re.I | re.S,
        )

    # Ensure #routes / sharedPurchase / sharedFooter preserved
    # Convert sharedFooter wrapper to footer element if it's a div
    body = re.sub(
        r'<div\s+id=["\']sharedFooter["\']\s*>\s*</div>',
        '<footer id="sharedFooter"></footer>',
        body,
        flags=re.I,
    )
    body = re.sub(
        r'<div\s+id=["\']sharedFooter["\']\s*></div>',
        '<footer id="sharedFooter"></footer>',
        body,
        flags=re.I,
    )

    # Insert nearby centres before sharedPurchase or footer
    nearby = nearby_html(meta, slug_to_name)
    if nearby and 'class="nearby-centres"' not in body:
        if 'id="sharedPurchase"' in body:
            body = body.replace(
                '<div id="sharedPurchase"></div>',
                nearby + '\n<div id="sharedPurchase"></div>',
                1,
            )
        elif 'id="sharedFooter"' in body:
            body = re.sub(
                r'(<(?:footer|div)\s+id=["\']sharedFooter["\'])',
                nearby + r"\n\1",
                body,
                count=1,
                flags=re.I,
            )

    # Wrap primary content in <main> if missing
    if "<main" not in body.lower():
        # Insert <main> after </header>, close before nearby/sharedPurchase
        if "</header>" in body:
            body = body.replace("</header>", "</header>\n<main>", 1)
            close_at = None
            for marker in (
                '<aside class="nearby-centres"',
                'id="sharedPurchase"',
                'id="sharedFooter"',
            ):
                idx = body.find(marker)
                if idx != -1:
                    close_at = idx
                    break
            if close_at is not None:
                body = body[:close_at] + "</main>\n" + body[close_at:]
            else:
                # before last container close
                body = re.sub(
                    r"(</div>\s*)(</div>\s*)?$",
                    r"</main>\n\1\2",
                    body,
                    count=1,
                )

    return body


def upgrade_page(path: Path, meta: dict, slug_to_name: dict[str, str]) -> dict:
    original = path.read_text(encoding="utf-8", errors="replace")
    faqs = extract_faqs_from_html(original)
    extra_head = extract_extra_head(original)
    body = extract_body_inner(original)

    body, txt_ref = strip_txt_fetch_scripts(body)
    body = strip_json_ld(body)

    inlined = None
    if txt_ref:
        txt_file = resolve_txt_path(txt_ref)
        if txt_file and txt_file.exists():
            inlined = txt_to_html(txt_file.read_text(encoding="utf-8", errors="replace"))

    body = ensure_landmarks_and_chrome(body, meta, slug_to_name, inlined)

    # Ensure GA present
    ga = GA_SNIPPET if "G-EJB69589QP" not in original else GA_SNIPPET

    og_title = meta["title"].replace(" | DriveFlow", "").strip()
    head = HEAD_TEMPLATE.format(
        ga=ga,
        description=esc(meta["description"]),
        canonical=esc(meta["canonical"]),
        og_title=esc(og_title),
        og_image=esc(OG_IMAGE),
        title=esc(meta["title"]),
        extra_head=extra_head,
    )

    # Update H1 if present and generic
    def fix_h1(m: re.Match) -> str:
        return f"<h1>{esc(meta['h1'])}</h1>"

    body = re.sub(r"<h1[^>]*>.*?</h1>", fix_h1, body, count=1, flags=re.I | re.S)

    json_ld = build_json_ld(meta, faqs)

    # Ensure shared.js at end
    body = re.sub(
        r'<script\s+src=["\']/shared\.js["\'][^>]*>\s*</script>\s*',
        "",
        body,
        flags=re.I,
    )
    body = body.rstrip() + f"\n\n{json_ld}\n\n<script src=\"/shared.js\" defer></script>\n"

    out = head + "\n<body>\n" + body.strip() + "\n</body>\n</html>\n"
    # Cleanup excess blank lines
    out = re.sub(r"\n{3,}", "\n\n", out)
    path.write_text(out, encoding="utf-8")
    return {
        "slug": meta["slug"],
        "faqs": len(faqs),
        "inlined_txt": bool(inlined),
        "nearby": len(meta.get("nearby") or []),
    }


def main() -> None:
    data = load_meta()
    centres = data["centres"]
    slug_to_name = {c["slug"]: c["displayName"] for c in centres}
    results = []
    missing = []
    for c in centres:
        path = ROOT / f"{c['slug']}-routes.html"
        if not path.exists():
            missing.append(c["slug"])
            continue
        results.append(upgrade_page(path, c, slug_to_name))
    print(f"Upgraded {len(results)} pages")
    print(f"With FAQ schema: {sum(1 for r in results if r['faqs'])}")
    print(f"Inlined txt: {sum(1 for r in results if r['inlined_txt'])}")
    if missing:
        print("Missing pages:", missing)


if __name__ == "__main__":
    main()
