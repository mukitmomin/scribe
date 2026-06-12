"""Shared state-dir bootstrap for scribe scripts."""
import os
from pathlib import Path

INTERESTS_TEMPLATE = """# scribe interests

# Themes you care about (used to derive arXiv queries).
themes:
  - large language model agents and tool use
  - retrieval-augmented generation and long context
  - efficient training and inference

# Extra keywords to bias scoring (free-form).
keywords:
  - evaluation
  - reasoning

# Topics to avoid (penalize in scoring).
avoid:
  - pure theory with no experiments

# Teaching depth: beginner | practitioner | expert
depth: practitioner
"""


def scribe_home() -> Path:
    root = Path(os.environ.get("SCRIBE_HOME") or (Path.home() / ".scribe"))
    return root


def ensure_state() -> Path:
    """Create $SCRIBE_HOME and subdirs. Seed interests.md if missing.

    Returns the home path. Prints a one-line notice to stderr when interests.md
    was just created so the user knows to edit it.
    """
    import sys

    root = scribe_home()
    for sub in ("digests", "inbox", "notes", "drafts"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    seen = root / "seen.json"
    if not seen.exists():
        seen.write_text("{}\n", encoding="utf-8")
    interests = root / "interests.md"
    if not interests.exists():
        interests.write_text(INTERESTS_TEMPLATE, encoding="utf-8")
        print(
            f"scribe: created {interests} — edit it before scanning.",
            file=sys.stderr,
        )
    return root
