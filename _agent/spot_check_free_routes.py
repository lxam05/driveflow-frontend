#!/usr/bin/env python3
"""Spot-check free route JSON against backend Maps links and OSRM coverage."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT.parent / "my-backend" / "data"
FREE = ROOT / "data" / "free-routes"
MAP = json.loads((ROOT / "_agent" / "backend_route_map.json").read_text())
COORD_RE = re.compile(r"(-?\d+\.\d+),(-?\d+\.\d+)")

CHECK = ["tallaght", "finglas", "raheny", "dun-laoghaire", "naas"]


def parse_waypoints(url: str) -> list[tuple[float, float]]:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    if "/@" in path:
        path = path.split("/@")[0]
    seen: set[tuple[float, float]] = set()
    out: list[tuple[float, float]] = []
    for lat_s, lon_s in COORD_RE.findall(path):
        key = (round(float(lat_s), 6), round(float(lon_s), 6))
        if key not in seen:
            seen.add(key)
            out.append((float(lat_s), float(lon_s)))
    return out


def main() -> None:
    slugs = sys.argv[1:] or CHECK
    ok = 0
    for slug in slugs:
        free_path = FREE / f"{slug}.json"
        if not free_path.exists():
            print(f"FAIL {slug}: missing {free_path.name}")
            continue
        free = json.loads(free_path.read_text())
        backend_file = MAP["map"][slug]
        backend = json.loads((BACKEND / backend_file).read_text())
        orig_url = backend["routes"][0]["link"]
        orig_wps = parse_waypoints(orig_url)
        clean_wps = parse_waypoints(free["googleMapsUrl"])
        paras = free.get("paragraphs", [])
        word_count = sum(len(p.split()) for p in paras)
        wp_match = len(orig_wps) == len(clean_wps)
        has_cta = free["googleMapsUrl"].startswith("https://www.google.com/maps/dir/")
        starts_from = paras and paras[0].lower().startswith("from ")
        status = "OK" if wp_match and has_cta and starts_from and word_count > 80 else "WARN"
        if status == "OK":
            ok += 1
        print(
            f"{status} {slug}: {len(orig_wps)} wps, {len(paras)} paras, {word_count} words, "
            f"steps={free.get('stepCount')}"
        )
        if not wp_match:
            print(f"  waypoint mismatch orig={len(orig_wps)} clean={len(clean_wps)} json={free.get('waypointCount')}")
    print(f"\n{ok}/{len(slugs)} passed")
    if ok < len(slugs):
        sys.exit(1)


if __name__ == "__main__":
    main()
