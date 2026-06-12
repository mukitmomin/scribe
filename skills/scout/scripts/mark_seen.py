#!/usr/bin/env python3
"""Mark arXiv ids as seen in $SCRIBE_HOME/seen.json."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from _state import ensure_state, scribe_home


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ids", nargs="+", required=True)
    args = p.parse_args()

    ensure_state()
    path = scribe_home() / "seen.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        seen = {}

    today = date.today().isoformat()
    added = 0
    for raw in args.ids:
        aid = raw.strip()
        # Strip any version suffix like 1234.5678v2.
        if "v" in aid:
            head, _, tail = aid.partition("v")
            if tail.isdigit():
                aid = head
        if not aid:
            continue
        if aid not in seen:
            added += 1
        seen[aid] = today

    path.write_text(json.dumps(seen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"marked {added} new, {len(args.ids) - added} already seen, total {len(seen)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
