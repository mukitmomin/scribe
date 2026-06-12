#!/usr/bin/env python3
"""Initialise $SCRIBE_HOME/memory/themes.json if it does not exist."""
from __future__ import annotations

import json
from datetime import date

from _state import scribe_home


def main() -> int:
    home = scribe_home()
    memory_dir = home / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    path = memory_dir / "themes.json"
    if path.exists():
        return 0
    seed = {
        "version": 1,
        "updated": date.today().isoformat(),
        "topics": [],
        "reported_ids": [],
    }
    path.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
