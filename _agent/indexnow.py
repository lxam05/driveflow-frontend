"""
IndexNow notifier for DriveFlow (Bing + participating engines).

Ownership key is hosted at:
  https://www.driveflow.ie/{KEY}.txt

Usage:
  python _agent/indexnow.py https://www.driveflow.ie/guides/example.html
  python _agent/indexnow.py --file _agent/.indexnow-pending
  python _agent/indexnow.py --wait 60 --file _agent/.indexnow-pending

Does not guarantee indexing — only notifies engines that URLs changed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
SITE_ROOT = AGENT_DIR.parent

HOST = "www.driveflow.ie"
KEY = "adf8990a8b56702fd4a51a0fd12da9ac"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
PENDING_PATH = AGENT_DIR / ".indexnow-pending"
SITE_ORIGIN = f"https://{HOST}"


def absolute_url(url_or_path: str) -> str:
    value = (url_or_path or "").strip()
    if not value:
        raise ValueError("Empty URL")
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if not value.startswith("/"):
        value = "/" + value
    return SITE_ORIGIN + value


def write_pending(urls: list[str]) -> Path:
    lines = [absolute_url(u) for u in urls]
    PENDING_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return PENDING_PATH


def read_pending(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(absolute_url(line))
    # de-dupe, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def submit(urls: list[str], *, timeout: float = 30.0) -> tuple[int, str]:
    """POST urlList to IndexNow. Returns (status_code, body)."""
    cleaned = [absolute_url(u) for u in urls]
    if not cleaned:
        raise ValueError("No URLs to submit")

    # IndexNow requires URLs to match the host exactly (www).
    for u in cleaned:
        if not u.startswith(SITE_ORIGIN + "/") and u != SITE_ORIGIN + "/":
            raise ValueError(f"URL host mismatch (expected {HOST}): {u}")

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": cleaned,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Submit URLs to IndexNow")
    parser.add_argument(
        "urls",
        nargs="*",
        help="Absolute or site-relative URLs to submit",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="File with one URL per line (default pending file if present)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=0,
        help="Seconds to sleep before submit (wait for GitHub Pages)",
    )
    args = parser.parse_args(argv)

    urls: list[str] = []
    if args.urls:
        urls.extend(args.urls)
    if args.file:
        urls.extend(read_pending(args.file))
    elif not args.urls and PENDING_PATH.exists():
        urls.extend(read_pending(PENDING_PATH))

    if not urls:
        print("No URLs to submit.")
        return 0

    # de-dupe
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        abs_u = absolute_url(u)
        if abs_u not in seen:
            seen.add(abs_u)
            unique.append(abs_u)

    if args.wait > 0:
        print(f"Waiting {args.wait}s for deploy/CDN...")
        time.sleep(args.wait)

    print(f"IndexNow submit ({len(unique)} URL(s)) → {ENDPOINT}")
    for u in unique:
        print(f"  - {u}")

    status, body = submit(unique)
    # 200 = OK, 202 = Accepted are both success for IndexNow
    if status in (200, 202):
        print(f"OK HTTP {status}" + (f" {body}" if body else ""))
        return 0

    print(f"FAILED HTTP {status}: {body}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
