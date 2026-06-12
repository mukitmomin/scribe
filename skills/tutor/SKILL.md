---
name: tutor
description: Teach an arXiv paper interactively in the terminal, section by section, matched to the user's depth, ending with a spaced-repetition note. Use for /scribe:learn or "teach me this paper".
---

# Tutor

State lives under the state dir, resolved in order: `$SCRIBE_HOME`, else
`./data/` if it exists in the current directory (repo-local mode for remote /
mobile sessions), else `~/.scribe/`. `<skill-dir>` means the directory
containing this SKILL.md.

## Setup

1. Read `$SCRIBE_HOME/interests.md` and note `depth` (beginner | practitioner
   | expert). It sets vocabulary, pace, and how much background you supply.
2. Pick the paper: the arXiv id the user gave, else the highest-score file in
   `$SCRIBE_HOME/inbox/`. If neither exists, say so, suggest /scribe:scan, stop.
3. Run `python3 <skill-dir>/scripts/fetch_paper.py --id <id>` → numbered
   section list + abstract. Fetch individual sections later with
   `--section N`, one at a time, only when the lesson needs them. NEVER fetch
   all sections up front. If the script reports full text unavailable, teach
   from the abstract and say the coverage is limited.

## Teaching sequence

This is a conversation, not a lecture. One stage per message; ask, then wait.

1. The problem and why it matters — from the abstract and intro.
2. The core idea in plain language. For beginner depth, lead with an analogy;
   for expert depth, lead with what differs from prior work.
3. Method walkthrough — fetch method sections on demand as you go.
4. Results and limitations — report actual numbers, and be honest about weak
   baselines or narrow evals.
5. Ask 2–3 checking questions, one at a time. If an answer is wrong or shaky,
   re-explain that piece a different way before continuing.

## Wrap-up

Write `$SCRIBE_HOME/notes/<id>.md`:

```
---
title: <title>
status: learned
learned: <today YYYY-MM-DD>
next_review: <today + 3 days>
interval_days: 3
---
## Summary
<=200 words.

## Key takeaways
3–5 bullets. Where the user phrased something well in their answers, use
their words.
```

Then delete `$SCRIBE_HOME/inbox/<id>.md` if it exists. Run
`python3 <skill-dir>/scripts/sync.py --label learn` to commit and push the
state dir when it is a git repo (no-op otherwise). Finally, tell the user the
note path and review date.
