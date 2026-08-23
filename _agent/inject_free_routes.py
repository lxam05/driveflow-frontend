#!/usr/bin/env python3
"""
Inject free route 1 cards and fix data-routes-insert-after anchor placement.

For each {slug}-routes.html:
  - Insert/replace .free-route-card after .centre-snapshot (skip maldron-hotel)
  - Move data-routes-insert-after to a dedicated anchor after free card
    (and after #routes-preview when present)

Usage:
  python3 _agent/inject_free_routes.py
  python3 _agent/inject_free_routes.py --slug tallaght --dry-run
  python3 _agent/inject_free_routes.py --force   # replace existing cards
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FREE_ROUTES_DIR = ROOT / "data" / "free-routes"
ROUTE_MAP_PATH = ROOT / "_agent" / "backend_route_map.json"

ANCHOR = '<div data-routes-insert-after aria-hidden="true"></div>'
CARD_RE = re.compile(
    r'\s*<section class="info-section free-route-card"[^>]*>[\s\S]*?</section>\s*',
    flags=re.I,
)


def load_free_route(slug: str) -> dict | None:
    path = FREE_ROUTES_DIR / f"{slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def direction_lines(route: dict) -> list[str]:
    lines = route.get("directions") or route.get("paragraphs") or []
    return [str(line).strip() for line in lines if str(line).strip()]


def card_html(route: dict) -> str:
    display = route["displayName"]
    short = re.sub(r"\s+Driving Test Centre$", "", display, flags=re.I)
    lines = direction_lines(route)
    body = "\n".join(f"                    <p>{html_lib.escape(line)}</p>" for line in lines)
    maps_url = html_lib.escape(route["googleMapsUrl"], quote=True)
    aria = html_lib.escape(f"{short} free sample route")
    title = html_lib.escape(f"{short} Free Driving Test Route")
    return f"""        <section class="info-section free-route-card" id="free-route-1" aria-label="{aria}">
            <details class="free-route-details">
                <summary class="free-route-summary">
                    <span class="free-route-toggle" aria-hidden="true"></span>
                    <span class="free-route-summary-title">{title}</span>
                    <span class="free-route-chevron" aria-hidden="true"></span>
                </summary>
                <div class="free-route-panel">
                    <p class="free-route-lede">A turn-by-turn practice route from the {html_lib.escape(short)} test centre. Follow it locally before test day.</p>
                    <div class="free-route-directions">
{body}
                    </div>
                    <p class="free-route-cta">
                        <a href="{maps_url}" target="_blank" rel="noopener noreferrer">Try the free Google Maps test route</a>
                    </p>
                </div>
            </details>
        </section>
"""


def strip_insert_after(html: str) -> str:
    return re.sub(r"\s*data-routes-insert-after", "", html)


def remove_card(html: str) -> str:
    return CARD_RE.sub("\n\n", html, count=1)


def find_snapshot_end(html: str) -> int | None:
    m = re.search(
        r'<section class="centre-snapshot"[^>]*>[\s\S]*?</section>',
        html,
        flags=re.I,
    )
    return m.end() if m else None


def find_preview_end(html: str) -> int | None:
    m = re.search(
        r'<div class="info-section" id="routes-preview"[^>]*>[\s\S]*?</div>',
        html,
        flags=re.I,
    )
    return m.end() if m else None


def find_card_end(html: str) -> int | None:
    m = CARD_RE.search(html)
    return m.end() if m else None


def remove_orphan_anchors(html: str) -> str:
    return re.sub(
        r'\s*<div data-routes-insert-after(?:\s[^>]*)?>\s*</div>\s*',
        "\n",
        html,
        flags=re.I,
    )


def inject_file(path: Path, skip_slugs: set[str], dry_run: bool = False, force: bool = False) -> str:
    slug = path.stem.replace("-routes", "")
    html = path.read_text(encoding="utf-8")
    original = html

    has_card = bool(CARD_RE.search(html))
    if has_card and not force and slug not in skip_slugs:
        return "skip (already injected)"

    html = strip_insert_after(html)
    html = remove_orphan_anchors(html)
    if has_card:
        html = remove_card(html)

    if slug not in skip_slugs:
        route = load_free_route(slug)
        if not route:
            return "error: missing free-route json"
        snap_end = find_snapshot_end(html)
        if snap_end is None:
            return "error: no centre-snapshot"
        card = card_html(route) + "\n"
        html = html[:snap_end] + "\n\n" + card + html[snap_end:]

    # Place anchor after preview > card > snapshot, before #routes
    if "data-routes-insert-after" not in html:
        insert_at = find_preview_end(html)
        if insert_at is None:
            insert_at = find_card_end(html)
        if insert_at is None:
            insert_at = find_snapshot_end(html)
        if insert_at is None:
            return "error: no insertion point"

        anchor_block = f"\n        {ANCHOR}\n"
        routes_m = re.search(r'\n\s*<div id="routes"', html[insert_at:], flags=re.I)
        if routes_m:
            pos = insert_at + routes_m.start()
            html = html[:pos] + anchor_block + html[pos:]
        else:
            html = html[:insert_at] + anchor_block + html[insert_at:]

    if html == original:
        return "unchanged"

    if not dry_run:
        path.write_text(html, encoding="utf-8")
    return "updated"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Process one centre only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace existing free-route cards")
    args = parser.parse_args()

    route_map = json.loads(ROUTE_MAP_PATH.read_text(encoding="utf-8"))
    skip_slugs = set(route_map.get("skip", []))

    if args.slug:
        paths = [ROOT / f"{args.slug}-routes.html"]
    else:
        paths = sorted(ROOT.glob("*-routes.html"))

    counts: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            print(f"MISSING {path.name}")
            continue
        result = inject_file(path, skip_slugs, args.dry_run, force=True)
        counts[result] = counts.get(result, 0) + 1
        print(f"{path.name}: {result}")

    print("\nSummary:", counts)


if __name__ == "__main__":
    main()
