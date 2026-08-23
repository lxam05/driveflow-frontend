#!/usr/bin/env python3
"""
Deterministic paragraph → one-line-per-direction splitter (no API).

Use when Claude reformat is unavailable. Splits on sentence ends and
common turn connectors so each direction is its own line.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FREE_DIR = ROOT / "data" / "free-routes"

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Split mid-sentence turn chains: ", then turn left…" / " then take the…"
TURN_SPLIT = re.compile(
    r",\s+(?="
    r"then\s+(?:turn|take|exit|bear|continue|left|right|1st|2nd|3rd|practice|park|follow)|"
    r"(?:turn|take|exit)\s+(?:left|right|the|1st|2nd|3rd)|"
    r"at\s+the\s+(?:end|lights|roundabout|junction|next)|"
    r"practice\s+a\b|"
    r"come\s+back\b|"
    r"to\s+return\b|"
    r"finish\s+(?:the|by)\b"
    r")",
    flags=re.I,
)
LEAD_THEN = re.compile(r"^then\s+", flags=re.I)


def clean_line(text: str) -> str:
    text = text.strip().strip(",; ")
    text = re.sub(r"\s+", " ", text)
    if not text:
        return ""
    # Drop trailing period for a cleaner line list (optional polish)
    if text.endswith(".") and not text.endswith("…"):
        text = text[:-1]
    return text[0].upper() + text[1:] if text else text


def paragraph_to_lines(paragraph: str) -> list[str]:
    lines: list[str] = []
    for sentence in SENTENCE_SPLIT.split(paragraph.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        chunks = TURN_SPLIT.split(sentence)
        for chunk in chunks:
            chunk = LEAD_THEN.sub("", chunk.strip())
            line = clean_line(chunk)
            if line and len(line) > 8:
                lines.append(line)
    return lines


def already_line_format(route: dict) -> bool:
    dirs = route.get("directions") or []
    if len(dirs) < 8:
        return False
    avg = sum(len(x) for x in dirs) / len(dirs)
    return avg < 200


def merge_fragments(lines: list[str]) -> list[str]:
    """Join orphan fragments like 'At the end of the road' with the next turn."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        while i + 1 < len(lines):
            has_action = bool(
                re.search(
                    r"\b(turn|take|exit|left|right|onto|into|practice|park|u-turn|roundabout|continue|follow|bear|keep|move|pull|finish|return)\b",
                    line,
                    flags=re.I,
                )
            )
            if len(line) >= 45 and has_action:
                break
            if len(line) >= 70:
                break
            nxt = lines[i + 1]
            joined = f"{line} {nxt[0].lower() + nxt[1:]}" if nxt else line
            line = clean_line(joined)
            i += 1
        out.append(line)
        i += 1
    return out


def convert_route(route: dict) -> list[str]:
    if already_line_format(route) and route.get("reformatMethod") != "local-split":
        return list(route["directions"])
    source = route.get("paragraphs") or route.get("directions") or []
    # Prefer original dense paragraphs if directions are already a broken local split
    # Re-run always uses paragraphs from file — after first local split paragraphs==directions
    # so keep a private backup? For pending we still have good paragraphs before overwrite.
    lines: list[str] = []
    for para in source:
        lines.extend(paragraph_to_lines(str(para)))
    out: list[str] = []
    for line in lines:
        if not out or out[-1].lower() != line.lower():
            out.append(line)
    if len(out) < 6:
        joined = " ".join(str(p) for p in source)
        out = [clean_line(x) for x in re.split(r"\s+then\s+", joined, flags=re.I) if clean_line(x)]
    return merge_fragments(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug")
    parser.add_argument("--only-pending", action="store_true")
    args = parser.parse_args()

    files = (
        [FREE_DIR / f"{args.slug}.json"]
        if args.slug
        else sorted(FREE_DIR.glob("*.json"))
    )

    ok = 0
    for path in files:
        route = json.loads(path.read_text(encoding="utf-8"))
        if args.only_pending and already_line_format(route):
            continue
        directions = convert_route(route)
        route["directions"] = directions
        route["paragraphs"] = directions
        route["reformattedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        route["reformatMethod"] = "local-split"
        path.write_text(json.dumps(route, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{path.stem}: {len(directions)} lines")
        ok += 1
    print(f"\nDone: {ok}")


if __name__ == "__main__":
    main()
