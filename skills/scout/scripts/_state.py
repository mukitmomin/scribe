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
    """Resolve the state directory, in order:

    1. ``$SCRIBE_HOME`` if set.
    2. ``./data/`` if it exists in the current directory (repo-local mode, for
       Claude Code web/mobile sessions where state is committed to the repo).
    3. ``~/.scribe/`` otherwise.
    """
    env = os.environ.get("SCRIBE_HOME")
    if env:
        return Path(env)
    local = Path.cwd() / "data"
    if local.is_dir():
        return local
    return Path.home() / ".scribe"


def ensure_state() -> Path:
    """Create the state dir and subdirs. Seed interests.md if missing.

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


def commit_and_push(label: str) -> None:
    """Commit and push the state dir if it is a git repo. Best-effort.

    Used by scout/tutor so remote (cron, mobile) sessions persist state to a
    private data repo. Skips silently when the state dir is not a git repo,
    warns to stderr if the push fails, and never raises or blocks the caller.
    """
    import subprocess
    import sys
    from datetime import date

    root = str(scribe_home())
    try:
        inside = subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return  # not a git repo — repo sync is opt-in

    message = f"scribe: {label} {date.today().isoformat()}"
    subprocess.run(["git", "-C", root, "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", root, "commit", "-m", message], capture_output=True)
    push = subprocess.run(
        ["git", "-C", root, "push"], capture_output=True, text=True
    )
    if push.returncode != 0:
        print(
            f"scribe: git push failed ({push.stderr.strip()})",
            file=sys.stderr,
        )
