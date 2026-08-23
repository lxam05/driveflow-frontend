#!/usr/bin/env python3
"""
Generate turn-by-turn free route 1 descriptions for centre pages.

Pipeline: backend JSON → parse Google Maps waypoints → OSRM steps →
Nominatim names → Claude polish → data/free-routes/{slug}.json

Usage:
  python3 _agent/generate_free_routes.py              # all centres
  python3 _agent/generate_free_routes.py --slug tallaght
  python3 _agent/generate_free_routes.py --dry-run

Requires: ANTHROPIC_API_KEY, pip install anthropic
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT.parent / "my-backend" / "data"
ROUTE_MAP_PATH = ROOT / "_agent" / "backend_route_map.json"
SEO_META_PATH = ROOT / "_agent" / "seo-centre-meta.json"
CENTRES_DIR = ROOT / "data" / "centres"
OUT_DIR = ROOT / "data" / "free-routes"

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "DriveFlowFreeRouteGenerator/1.0 (contact: liam@driveflow.ie)"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")

COORD_RE = re.compile(r"(-?\d+\.\d+),(-?\d+\.\d+)")

STYLE_RULES = """
**Mandatory style rules:**
- Never use the em dash character. Use commas, periods, or parentheses instead.
- Use "practice" and "practicing", not "practise" or "practising".
- Write for Irish learner drivers preparing for the RSA Category B test.
- Use plain turn-by-turn language: "exit left", "1st right", "at the lights", "take the roundabout 2nd exit".
- Reference real road names from the step data only. Do not invent RSA claims or examiner quotes.
- Do not mention DriveFlow, paywalls, or unlocking routes.
- ONE instruction per line (array item). Never write dense multi-turn paragraphs.
- Style like: "From {centre} exit left onto Broomhill Road towards the Greenhills Road"
  then next line: "On the Greenhills Road turn left and then the 1st right into …"
- First line must start with "From {centre label}…" using the provided centre address/name.
- End by returning toward the test centre when the route loops back.
- Aim for roughly 12–35 lines.
"""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def http_get(url: str, headers: dict | None = None) -> dict | list:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def parse_waypoints(maps_url: str) -> list[tuple[float, float]]:
    """Extract lat,lon pairs from a Google Maps /dir/ URL (excludes /@ viewport)."""
    parsed = urllib.parse.urlparse(maps_url)
    path = parsed.path
    if "/@" in path:
        path = path.split("/@")[0]
    coords: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for lat_s, lon_s in COORD_RE.findall(path):
        lat, lon = float(lat_s), float(lon_s)
        key = (round(lat, 6), round(lon, 6))
        if key not in seen:
            seen.add(key)
            coords.append((lat, lon))
    if len(coords) < 2:
        raise ValueError(f"Could not parse waypoints from URL: {maps_url[:120]}")
    return coords


def clean_maps_url(maps_url: str) -> str:
    """Keep waypoint coordinates; strip viewport and tracking params."""
    waypoints = parse_waypoints(maps_url)
    parts = [f"{lat},{lon}" for lat, lon in waypoints]
    return "https://www.google.com/maps/dir/" + "/".join(parts)


def osrm_steps(waypoints: list[tuple[float, float]]) -> list[dict]:
    """Fetch merged driving steps from OSRM between all waypoints."""
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in waypoints)
    url = (
        f"{OSRM_BASE}/{coord_str}"
        "?overview=false&steps=true&geometries=geojson&annotations=false"
    )
    data = http_get(url)
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {data.get('message', data)}")

    steps: list[dict] = []
    for leg in data["routes"][0]["legs"]:
        for step in leg["steps"]:
            maneuver = step.get("maneuver", {})
            steps.append(
                {
                    "instruction": maneuver.get("type", ""),
                    "modifier": maneuver.get("modifier", ""),
                    "name": (step.get("name") or "").strip(),
                    "distance_m": round(step.get("distance", 0)),
                    "location": maneuver.get("location", []),
                }
            )
    return steps


def nominatim_name(lat: float, lon: float) -> str:
    """Reverse-geocode a junction; rate-limited to 1 req/s."""
    params = urllib.parse.urlencode(
        {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
        }
    )
    url = f"{NOMINATIM_BASE}?{params}"
    try:
        data = http_get(url, headers={"User-Agent": USER_AGENT})
    except urllib.error.HTTPError:
        return ""
    time.sleep(1.05)
    addr = data.get("address", {})
    for key in ("road", "residential", "pedestrian", "suburb", "neighbourhood"):
        if addr.get(key):
            return addr[key]
    return data.get("display_name", "").split(",")[0]


def enrich_steps(steps: list[dict], max_geocodes: int = 12) -> list[dict]:
    """Add Nominatim names for key unnamed junctions (rate-limited)."""
    turn_mods = {"left", "right", "slight left", "slight right", "sharp left", "sharp right"}
    candidates: list[int] = []
    if steps:
        candidates.append(0)
    for i, step in enumerate(steps):
        if step["name"]:
            continue
        mod = (step.get("modifier") or "").lower()
        typ = (step.get("instruction") or "").lower()
        if mod in turn_mods or typ in {"roundabout", "rotary", "fork", "merge", "end of road"}:
            candidates.append(i)
    if len(steps) > 1 and (len(steps) - 1) not in candidates:
        candidates.append(len(steps) - 1)

    seen: set[int] = set()
    ordered: list[int] = []
    for idx in candidates:
        if idx not in seen:
            seen.add(idx)
            ordered.append(idx)
    if len(ordered) > max_geocodes:
        stride = max(1, len(ordered) // max_geocodes)
        ordered = ordered[::stride][:max_geocodes]

    last_geocode = 0.0
    for idx in ordered:
        step = steps[idx]
        if step["name"]:
            continue
        loc = step.get("location") or []
        if len(loc) != 2:
            continue
        lon, lat = loc
        now = time.time()
        wait = 1.05 - (now - last_geocode)
        if wait > 0:
            time.sleep(wait)
        name = nominatim_name(lat, lon)
        last_geocode = time.time()
        if name:
            step["name"] = name
    return steps


def format_step_line(step: dict) -> str:
    mod = step.get("modifier") or ""
    typ = step.get("instruction") or ""
    name = step.get("name") or "unnamed road"
    dist = step.get("distance_m", 0)
    parts = [typ]
    if mod:
        parts.append(mod)
    parts.append(name)
    if dist > 30:
        parts.append(f"({dist}m)")
    return " ".join(parts)


def build_raw_outline(steps: list[dict]) -> str:
    lines = []
    for step in steps:
        line = format_step_line(step)
        if line.strip() and line not in lines[-3:]:
            lines.append(line)
    return "\n".join(lines)


def centre_info(slug: str, meta: dict, first_wp: tuple[float, float]) -> dict:
    """Resolve display name and address for a centre."""
    display = meta.get("displayName", slug.replace("-", " ").title())
    address = ""
    centre_json = CENTRES_DIR / f"{slug}.json"
    if centre_json.exists():
        cfg = load_json(centre_json)
        c = cfg.get("centre", {})
        parts = [c.get("streetAddress"), c.get("addressLocality"), c.get("postalCode")]
        address = ", ".join(p for p in parts if p)
        if c.get("name"):
            display = c["name"]
    if not address:
        address = meta.get("location") or display
    return {"displayName": display, "centreAddress": address, "slug": slug}


def claude_polish(
    client: anthropic.Anthropic,
    centre: dict,
    raw_steps: str,
    google_url: str,
) -> list[str]:
    prompt = f"""Convert these OSRM driving steps into a simple line-by-line direction list
for a free sample Route 1 at the {centre['displayName']} RSA driving test centre in Ireland.

Centre: {centre['displayName']}
Address: {centre['centreAddress']}

Raw OSRM steps:
{raw_steps}

Google Maps reference (for your context only — do not mention this link in the output):
{google_url}

{STYLE_RULES}

Return ONLY valid JSON in this exact shape (no markdown fences):
{{"directions": ["From … exit left onto …", "On … turn left …", "..."]}}
"""
    message = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    data = json.loads(text)
    directions = [d.strip() for d in data.get("directions", []) if d and str(d).strip()]
    if not directions:
        # Back-compat if model still returns paragraphs
        directions = [d.strip() for d in data.get("paragraphs", []) if d and str(d).strip()]
    if len(directions) < 6:
        raise ValueError(f"Claude returned too few directions ({len(directions)})")
    return directions


def generate_one(
    slug: str,
    backend_file: str,
    meta_by_slug: dict,
    client: anthropic.Anthropic | None,
    dry_run: bool = False,
) -> dict | None:
    backend_path = BACKEND_DIR / backend_file
    data = load_json(backend_path)
    routes = data.get("routes") or []
    if not routes or not routes[0].get("link"):
        print(f"  SKIP {slug}: no route 1 link")
        return None

    maps_url = routes[0]["link"]
    waypoints = parse_waypoints(maps_url)
    clean_url = clean_maps_url(maps_url)
    meta = meta_by_slug.get(slug, {})
    centre = centre_info(slug, meta, waypoints[0])

    print(f"  {slug}: {len(waypoints)} waypoints, fetching OSRM…")
    steps = osrm_steps(waypoints)
    steps = enrich_steps(steps)
    raw = build_raw_outline(steps)

    if dry_run:
        print(f"  DRY RUN — {len(steps)} steps, raw preview:\n{raw[:400]}…")
        return None

    if client is None:
        raise RuntimeError("ANTHROPIC_API_KEY required for generation")

    print(f"  {slug}: Claude polish…")
    directions = claude_polish(client, centre, raw, clean_url)

    return {
        "slug": slug,
        "displayName": centre["displayName"],
        "centreAddress": centre["centreAddress"],
        "googleMapsUrl": clean_url,
        "directions": directions,
        "paragraphs": directions,  # alias for older injectors
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "waypointCount": len(waypoints),
        "stepCount": len(steps),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate free route 1 JSON for centre pages")
    parser.add_argument("--slug", help="Generate a single centre slug only")
    parser.add_argument("--dry-run", action="store_true", help="Parse/OSRM only, no Claude output")
    args = parser.parse_args()

    route_map = load_json(ROUTE_MAP_PATH)
    skip = set(route_map.get("skip", []))
    centre_map: dict[str, str] = route_map["map"]

    seo = load_json(SEO_META_PATH)
    meta_by_slug = {c["slug"]: c for c in seo.get("centres", [])}

    slugs = [args.slug] if args.slug else sorted(centre_map)
    if args.slug and args.slug in skip:
        print(f"ERROR: {args.slug} is in skip list")
        sys.exit(1)
    if args.slug and args.slug not in centre_map:
        print(f"ERROR: unknown slug {args.slug}")
        sys.exit(1)

    client = None
    if not args.dry_run:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY not set")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for slug in slugs:
        if slug in skip:
            continue
        try:
            result = generate_one(slug, centre_map[slug], meta_by_slug, client, args.dry_run)
            if result:
                out_path = OUT_DIR / f"{slug}.json"
                out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"  Wrote {out_path.name}")
                ok += 1
        except Exception as exc:
            print(f"  ERROR {slug}: {exc}")
            if args.slug:
                sys.exit(1)

    print(f"\nDone: {ok} route(s) written to {OUT_DIR}")


if __name__ == "__main__":
    main()
