#!/usr/bin/env python3
"""Emit JSONL of notes whose next_review <= today.

Reads $SCRIBE_HOME/notes/*.md, parses a minimal YAML-ish frontmatter block.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

from _state import ensure_state, scribe_home


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.parse_args()

    ensure_state()
    today = date.today()
    notes_dir = scribe_home() / "notes"
    if not notes_dir.exists():
        return 0

    for path in sorted(notes_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"scribe: read {path} failed: {e}", file=sys.stderr)
            continue
        fm = parse_frontmatter(text)
        nr = fm.get("next_review")
        if not nr:
            continue
        try:
            nr_date = date.fromisoformat(nr)
        except ValueError:
            print(f"scribe: bad next_review in {path.name}: {nr!r}", file=sys.stderr)
            continue
        if nr_date > today:
            continue
        try:
            interval = int(fm.get("interval_days") or 3)
        except ValueError:
            interval = 3
        record = {
            "id": path.stem,
            "title": fm.get("title", ""),
            "next_review": nr,
            "interval_days": interval,
        }
        sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
