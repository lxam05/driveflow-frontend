#!/usr/bin/env python3
"""
Migrate *-routes.html pages toward the canonical centre template:
- CSO snapshot above unlock
- data-routes-insert-after + noscript preview
- #routes immediately after preview
- pass-rate/waiting block with CSO citation
- Liam O'Connor byline + WebPage author in JSON-LD
"""
from __future__ import annotations

import html as html_lib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATS = json.loads((ROOT / "data" / "centre-stats.json").read_text(encoding="utf-8"))
CITATION = STATS["citation"]
LABEL = STATS["lastUpdatedLabel"]
NATIONAL = STATS["national"]["passRate"]
AUTHOR_BLOCK = (
    '        <p class="author-byline">Written by '
    '<a href="/about.html">Liam O\'Connor</a>. '
    f"Centre statistics last updated {LABEL}.</p>\n"
)


def fmt_rate(v) -> str:
    if v is None:
        return None
    return f"{v:g}%" if isinstance(v, float) else f"{v}%"


def fmt_weeks(v) -> str:
    if v is None:
        return None
    if isinstance(v, float) and v != int(v):
        return f"{v:g} weeks"
    return f"{int(v)} weeks"


def pass_dd(display: str, rate) -> str:
    if rate is None:
        return (
            f"Category B pass rate not published for this centre in the {LABEL} CSO release. "
            f"{html_lib.escape(CITATION)}"
        )
    nat = NATIONAL
    if rate > nat + 1:
        cmp_ = f"above the {nat:g}% national Category B average"
    elif rate < nat - 1:
        cmp_ = f"below the {nat:g}% national Category B average"
    else:
        cmp_ = f"close to the {nat:g}% national Category B average"
    return (
        f"{fmt_rate(rate)} Category B — {cmp_}. "
        f"{html_lib.escape(CITATION)} Last updated {LABEL}."
    )


def wait_dd(wait) -> str:
    if wait is None:
        return (
            f"Invite waiting time not published for this centre in the {LABEL} CSO release. "
            f"Check MyRoadSafety for live slots. {html_lib.escape(CITATION)}"
        )
    return (
        f"{fmt_weeks(wait)} to driving test invite (CSO month-end figure). "
        f"Live availability moves — confirm on MyRoadSafety. "
        f"{html_lib.escape(CITATION)} Last updated {LABEL}."
    )


def snapshot_html(slug: str, display: str, rate, wait) -> str:
    # Paywall inserts after snapshot when there is no real corridor preview list.
    return f"""        <section class="centre-snapshot" data-routes-insert-after aria-label="{html_lib.escape(display)} test centre snapshot">
            <h2>{html_lib.escape(display)} test centre snapshot</h2>
            <dl>
                <dt>Pass rate</dt>
                <dd>{pass_dd(display, rate)}</dd>
                <dt>Waiting time</dt>
                <dd>{wait_dd(wait)}</dd>
                <dt>Test length</dt>
                <dd>Drive typically 30–40 minutes and at least 7.5&nbsp;km, plus signs, questions and technical checks.</dd>
                <dt>Typical manoeuvres</dt>
                <dd>Reverse around corner, turnabout, hill start (RSA car test).</dd>
            </dl>
            <p class="snapshot-note">{html_lib.escape(CITATION)} Always confirm the exact centre address on your RSA booking letter.</p>
        </section>

"""


def ensure_snapshot_insert_after(html: str) -> str:
    """Put data-routes-insert-after on centre-snapshot when no real routes-preview exists."""
    if 'id="routes-preview"' in html and "data-routes-insert-after" in html:
        return html
    if re.search(
        r'<section class="centre-snapshot"[^>]*data-routes-insert-after',
        html,
        flags=re.I,
    ):
        return html
    return re.sub(
        r'(<section class="centre-snapshot")(?![^>]*data-routes-insert-after)',
        r"\1 data-routes-insert-after",
        html,
        count=1,
        flags=re.I,
    )


def pass_waiting_html(slug: str, display: str, rate, wait) -> str:
    rate_txt = (
        f"<strong>{fmt_rate(rate)}</strong> Category B"
        if rate is not None
        else "not published in the latest CSO monthly release"
    )
    wait_txt = (
        f"<strong>{fmt_weeks(wait)}</strong> to invite"
        if wait is not None
        else "not published in the latest CSO monthly release"
    )
    return f"""        <div class="info-section" id="pass-rate-waiting">
            <h2>What is the {html_lib.escape(display)} pass rate and waiting time?</h2>
            <p><strong>Pass rate:</strong> {rate_txt}. {html_lib.escape(CITATION)}</p>
            <p><strong>Waiting time:</strong> {wait_txt}. Check MyRoadSafety for live slots and cancellations. {html_lib.escape(CITATION)} Last updated {LABEL}.</p>
            <p>Compare every centre on our <a href="/guides/driving-test-pass-rates-by-centre.html">pass rates ranking</a> and <a href="/guides/driving-test-waiting-times-by-centre.html">waiting times ranking</a>.</p>
        </div>

"""


def extract_routes_block(html: str) -> tuple[str | None, str]:
    m = re.search(
        r'<div id="routes" class="routes-section"[^>]*>\s*</div>',
        html,
        flags=re.I,
    )
    if not m:
        return None, html
    block = m.group(0)
    return block, html[: m.start()] + html[m.end() :]


def ensure_author_byline(html: str) -> str:
    if "author-byline" in html:
        return html
    # Insert before nearby or sharedPurchase
    for marker in (
        '<aside class="nearby-centres"',
        '<div id="sharedPurchase">',
        '<footer id="sharedFooter">',
    ):
        idx = html.find(marker)
        if idx != -1:
            return html[:idx] + AUTHOR_BLOCK + html[idx:]
    return html + AUTHOR_BLOCK


def ensure_webpage_author(html: str) -> str:
    if '"@type": "Person"' in html and "Liam O'Connor" in html:
        return html
    # Inject author into first WebPage object if present
    pattern = re.compile(
        r'("@type"\s*:\s*"WebPage"[^}]*?"publisher"\s*:\s*\{[^}]*\})',
        re.S,
    )

    def repl(m: re.Match) -> str:
        chunk = m.group(1)
        if '"author"' in chunk:
            return chunk
        return chunk.replace(
            '"publisher"',
            '"author": {"@type": "Person", "name": "Liam O\'Connor", "url": "https://www.driveflow.ie/about.html"},\n      "publisher"',
            1,
        )

    new_html, n = pattern.subn(repl, html, count=1)
    return new_html if n else html


def update_existing_snapshot(html: str, display: str, rate, wait) -> str:
    # Replace first Pass rate / Waiting time dd pairs inside centre-snapshot
    snap = re.search(
        r'(<section class="centre-snapshot"[\s\S]*?</section>)',
        html,
        flags=re.I,
    )
    if not snap:
        return html
    block = snap.group(1)
    block2 = re.sub(
        r"(<dt>\s*Pass rate\s*</dt>\s*<dd>)[\s\S]*?(</dd>)",
        lambda m: m.group(1) + pass_dd(display, rate) + m.group(2),
        block,
        count=1,
        flags=re.I,
    )
    block2 = re.sub(
        r"(<dt>\s*Waiting time\s*</dt>\s*<dd>)[\s\S]*?(</dd>)",
        lambda m: m.group(1) + wait_dd(wait) + m.group(2),
        block2,
        count=1,
        flags=re.I,
    )
    # Update snapshot-note citation if present
    note = (
        html_lib.escape(CITATION)
        + " Always confirm the exact centre address on your RSA booking letter."
    )
    block2 = re.sub(
        r'(<p class="snapshot-note">)[\s\S]*?(</p>)',
        lambda m: m.group(1) + note + m.group(2),
        block2,
        count=1,
        flags=re.I,
    )
    return html[: snap.start()] + block2 + html[snap.end() :]


def update_pass_waiting_section(html: str, display: str, rate, wait) -> str:
    section = pass_waiting_html(display, display, rate, wait)
    if 'id="pass-rate-waiting"' in html:
        return re.sub(
            r'<div class="info-section" id="pass-rate-waiting">[\s\S]*?</div>\s*',
            section,
            html,
            count=1,
            flags=re.I,
        )
    # Insert before tips/faq/nearby/author/sharedPurchase
    for marker in (
        'id="tips"',
        'id="faq"',
        'class="author-byline"',
        '<aside class="nearby-centres"',
        '<div id="sharedPurchase">',
    ):
        # find a sensible parent start
        if marker.startswith("id="):
            m = re.search(rf'<div class="info-section" {marker}>', html)
            if m:
                return html[: m.start()] + section + html[m.start() :]
        else:
            idx = html.find(marker)
            if idx != -1:
                return html[:idx] + section + html[idx:]
    return html


def update_stamp(html: str) -> str:
    # Only touch explicit "Updated MONTH YEAR" stamps, not phrases like "last updated".
    html = re.sub(
        r"(?<![A-Za-z])Updated (January|February|March|April|May|June|July|August|September|October|November|December)\s+2026",
        f"Updated {LABEL}",
        html,
        flags=re.I,
    )
    return html


def migrate_file(path: Path) -> str:
    slug = path.stem.replace("-routes", "")
    stats = STATS["centres"].get(slug, {})
    display = stats.get("displayName") or slug.replace("-", " ").title()
    rate = stats.get("passRate")
    wait = stats.get("waitWeeks")

    html = path.read_text(encoding="utf-8")
    original = html

    html = update_stamp(html)

    if 'class="centre-snapshot"' in html:
        html = update_existing_snapshot(html, display, rate, wait)
    else:
        # Inject snapshot + preview after header; move routes after preview
        routes_block, html = extract_routes_block(html)
        if routes_block is None:
            # create routes block from data-route if present elsewhere
            m = re.search(r'data-route="([^"]+)"', html)
            rk = m.group(1) if m else slug
            routes_block = (
                f'<div id="routes" class="routes-section" data-route="{rk}" '
                f'style="scroll-margin-top: 120px;"></div>'
            )

        insert = snapshot_html(slug, display, rate, wait)
        insert += "        " + routes_block + "\n\n"

        m = re.search(r"</header>", html, flags=re.I)
        if not m:
            raise RuntimeError(f"No </header> in {path.name}")
        html = html[: m.end()] + "\n\n" + insert + html[m.end() :]

        # If a leftover empty routes div remains, remove duplicates
        seen = 0

        def dedupe(match: re.Match) -> str:
            nonlocal seen
            seen += 1
            return match.group(0) if seen == 1 else ""

        html = re.sub(
            r'\s*<div id="routes" class="routes-section"[^>]*>\s*</div>',
            dedupe,
            html,
            flags=re.I,
        )

    # Never re-inject a generic routes-preview. Ensure paywall anchors after snapshot
    # unless a real #routes-preview (with corridor bullets) already owns the insert attribute.
    html = ensure_snapshot_insert_after(html)

    html = update_pass_waiting_section(html, display, rate, wait)
    html = ensure_author_byline(html)
    html = ensure_webpage_author(html)

    # Tighten FAQ pass/wait answers when obvious patterns exist
    if rate is not None:
        ans = (
            f"The Category B pass rate at {display} was {fmt_rate(rate)} in {LABEL}. {CITATION}"
        )
        html = re.sub(
            r"(What is the [^<]*pass rate\?</h3>\s*<p>)[\s\S]*?(</p>)",
            lambda m: m.group(1) + ans + m.group(2),
            html,
            count=1,
            flags=re.I,
        )
    if wait is not None:
        ans = (
            f"CSO reported {fmt_weeks(wait)} to driving test invite at month end ({LABEL}). "
            f"Confirm live slots on MyRoadSafety. {CITATION}"
        )
        html = re.sub(
            r"(How long is the waiting time for a [^<]*\?</h3>\s*<p>)[\s\S]*?(</p>)",
            lambda m: m.group(1) + ans + m.group(2),
            html,
            count=1,
            flags=re.I,
        )

    if html != original:
        path.write_text(html, encoding="utf-8")
        return "updated"
    return "unchanged"


def main() -> None:
    paths = sorted(
        p for p in ROOT.glob("*-routes.html") if p.parent == ROOT
    )
    counts = {"updated": 0, "unchanged": 0}
    for path in paths:
        status = migrate_file(path)
        counts[status] += 1
        print(f"{status:9} {path.name}")
    print(counts)


if __name__ == "__main__":
    main()
