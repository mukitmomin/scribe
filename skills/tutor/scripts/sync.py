#!/usr/bin/env python3
"""Commit and push scribe state when the state dir is a git repo (best-effort).

No-op when the state dir is not a git repo. Never blocks: a failed push warns
to stderr and still exits 0.
"""
from __future__ import annotations

import argparse
import sys

from _state import commit_and_push


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--label", required=True, help="command name, e.g. scan or learn")
    args = p.parse_args()
    commit_and_push(args.label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
