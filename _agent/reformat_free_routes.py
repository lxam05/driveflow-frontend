#!/usr/bin/env python3
"""
Reformat free-route JSON from dense paragraphs into one-direction-per-line lists.

Matches the Tallaght Route 1 style: each turn / junction instruction on its own line.

Usage:
  _agent/.venv/bin/python _agent/reformat_free_routes.py
  _agent/.venv/bin/python _agent/reformat_free_routes.py --slug tallaght
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic (use _agent/.venv)")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FREE_DIR = ROOT / "data" / "free-routes"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")

PROMPT = """Rewrite these driving-test route paragraphs as a simple line-by-line direction list
for Irish learner drivers (RSA Category B).

Centre: {display}
Address: {address}

Source paragraphs:
{paragraphs}

Rules:
- Return ONE instruction per array item (one direction / turn / roundabout / manoeuvre per line).
- Style like this example (each line is separate):
  "From Tallaght Driving Test Centre 51 Broomhill Road exit left onto the Broomhill Road towards the Greenhills Road"
  "On the Greenhills Road turn left and then the 1st right into the Hibernian Industrial Estate."
  "Take the 1st right (after Power City) then a right at the T Junction to continue back towards the Greenhills Road."
  "At the lights take the left turn onto the Tallaght Main Road."
  "Park after the junction and reverse around the corner."
- Keep real road names from the source. Do not invent places.
- Use plain language: exit left, 1st right, at the lights, take the roundabout 2nd exit.
- First line must start with "From …".
- Last few lines should bring the driver back toward the test centre when the route loops back.
- Never use the em dash character.
- Use "practice" / "practicing", not "practise".
- Do not number the lines. Do not mention DriveFlow or paywalls.
- Aim for roughly 12–35 lines (not one giant paragraph, not hundreds of tiny fragments).

Return ONLY valid JSON (no markdown fences):
{{"directions": ["line one", "line two", "..."]}}
"""


def convert_one(client: anthropic.Anthropic, route: dict) -> list[str]:
    paragraphs = route.get("directions") or route.get("paragraphs") or []
    if isinstance(paragraphs, list) and paragraphs and all(
        isinstance(p, str) and len(p) < 180 for p in paragraphs
    ) and len(paragraphs) >= 8:
        # Already looks line-like; keep if user re-runs
        pass

    text_block = "\n\n".join(paragraphs) if isinstance(paragraphs, list) else str(paragraphs)
    prompt = PROMPT.format(
        display=route.get("displayName", route.get("slug", "")),
        address=route.get("centreAddress", ""),
        paragraphs=text_block,
    )
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
    directions = [d.strip() for d in data.get("directions", []) if d and d.strip()]
    if len(directions) < 6:
        raise ValueError(f"too few directions ({len(directions)})")
    return directions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    files = (
        [FREE_DIR / f"{args.slug}.json"]
        if args.slug
        else sorted(FREE_DIR.glob("*.json"))
    )

    ok = 0
    for path in files:
        if not path.exists():
            print(f"MISSING {path.name}")
            continue
        route = json.loads(path.read_text(encoding="utf-8"))
        print(f"  {route.get('slug', path.stem)}…")
        try:
            directions = convert_one(client, route)
            route["directions"] = directions
            # Keep paragraphs for backwards compat but prefer directions
            route["paragraphs"] = directions
            route["reformattedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            path.write_text(json.dumps(route, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"    → {len(directions)} lines")
            ok += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            if args.slug:
                sys.exit(1)

    print(f"\nDone: {ok}/{len(files)} reformatted")


if __name__ == "__main__":
    main()
