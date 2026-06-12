#!/usr/bin/env python3
"""Post the top papers from today's digest to Slack using Block Kit.

Reads the digest for scores/links and the corresponding inbox files for
summaries. Posts a formatted Block Kit message with clickable arXiv links.
Marks notified papers as reported (status: reported) on success.
Never blocks a scan: all failures warn to stderr and exit 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from _state import scribe_home

ARXIV_URL = re.compile(r"arxiv\.org/abs/([^\s)\]|]+)", re.IGNORECASE)
FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_digest(text: str, limit: int = 5) -> list[dict]:
    rows: list[dict] = []
    header_seen = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not header_seen:
            header_seen = True
            continue
        if all(set(c) <= {"-", ":", " "} for c in cells):
            continue
        if len(cells) < 4:
            continue
        m = ARXIV_URL.search(line)
        if not m:
            continue
        rows.append({"id": m.group(1), "score": cells[0], "title": cells[1]})
        if len(rows) >= limit:
            break
    return rows


def read_inbox(home: Path, arxiv_id: str) -> dict:
    """Return frontmatter fields from inbox/<id>.md, or empty dict."""
    path = home / "inbox" / f"{arxiv_id}.md"
    if not path.exists():
        return {}
    m = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ": " in line:
            k, _, v = line.partition(": ")
            result[k.strip()] = v.strip().strip('"')
    return result


def mark_reported(home: Path, arxiv_id: str) -> None:
    path = home / "inbox" / f"{arxiv_id}.md"
    if not path.exists():
        return
    today = date.today().isoformat()
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^status: \S+", f"status: reported", text, flags=re.MULTILINE)
    if "reported_at:" not in text:
        text = re.sub(
            r"^(status: reported)",
            f"\\1\nreported_at: {today}",
            text,
            flags=re.MULTILINE,
        )
    path.write_text(text, encoding="utf-8")


def build_blocks(papers: list[dict], home: Path, fetched: int, inboxed: int, today: str) -> list:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"scribe — {today}"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"fetched {fetched} · inboxed {inboxed}"}],
        },
        {"type": "divider"},
    ]

    for p in papers:
        fm = read_inbox(home, p["id"])
        if fm.get("status") == "reported":
            continue
        summary = fm.get("summary") or fm.get("reason", "")
        url = f"https://arxiv.org/abs/{p['id']}"
        title_link = f"<{url}|{p['title']}>"
        text = f"*[{p['score']}]* {title_link}"
        if summary:
            text += f"\n_{summary}_"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})

    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetched", type=int, default=0)
    ap.add_argument("--inboxed", type=int, default=0)
    args = ap.parse_args()

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return 0

    home = scribe_home()
    today = date.today().isoformat()
    digest = home / "digests" / f"{today}.md"
    if not digest.exists():
        print(f"scribe: no digest at {digest}", file=sys.stderr)
        return 0

    papers = parse_digest(digest.read_text(encoding="utf-8"))
    if not papers:
        print("scribe: digest had no parseable rows", file=sys.stderr)
        return 0

    blocks = build_blocks(papers, home, args.fetched, args.inboxed, today)
    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except (urllib.error.URLError, OSError) as e:
        print(f"scribe: slack post failed ({e})", file=sys.stderr)
        return 0

    for p in papers:
        mark_reported(home, p["id"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
