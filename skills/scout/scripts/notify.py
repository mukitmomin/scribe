#!/usr/bin/env python3
"""Post the top papers from today's digest to a Slack incoming webhook.

Reads ``<state>/digests/<today>.md``, pulls the top 5 rows of the ranked table,
and POSTs them as plain ranked lines to ``$SLACK_WEBHOOK_URL``. A no-op (exit 0)
when the webhook is unset. Never blocks a scan: any failure warns to stderr and
still exits 0.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date

from _state import scribe_home

ARXIV_URL = re.compile(r"arxiv\.org/abs/([^\s)\]|]+)", re.IGNORECASE)


def parse_digest(text: str, limit: int = 5) -> list[str]:
    """Extract up to ``limit`` "score — title — url" lines from a digest table.

    The digest is a markdown table (Score | Title | Reason | Link) sorted by
    score descending, so the first rows are the top papers.
    """
    rows: list[str] = []
    header_seen = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not header_seen:  # first table row is the header
            header_seen = True
            continue
        if all(set(c) <= {"-", ":", " "} for c in cells):  # separator row
            continue
        if len(cells) < 2:
            continue
        m = ARXIV_URL.search(line)
        if not m:
            continue
        score, title = cells[0], cells[1]
        rows.append(f"{score} — {title} — https://arxiv.org/abs/{m.group(1)}")
        if len(rows) >= limit:
            break
    return rows


def main() -> int:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return 0  # notifications disabled

    digest = scribe_home() / "digests" / f"{date.today().isoformat()}.md"
    if not digest.exists():
        print(f"scribe: no digest at {digest}; nothing to notify", file=sys.stderr)
        return 0

    rows = parse_digest(digest.read_text(encoding="utf-8"))
    if not rows:
        print("scribe: digest had no parseable rows; nothing to notify", file=sys.stderr)
        return 0

    payload = "scribe — today's top papers\n" + "\n".join(rows)
    data = json.dumps({"text": payload}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except (urllib.error.URLError, OSError) as e:
        print(f"scribe: slack post failed ({e})", file=sys.stderr)
        return 0  # never block the scan
    return 0


if __name__ == "__main__":
    sys.exit(main())
