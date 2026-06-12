---
name: reviewer
description: Spaced-repetition quiz over previously learned paper notes that are due for review, rescheduling each by recall quality. Use for /scribe:review.
---

# Reviewer

State lives under the state dir, resolved in order: `$SCRIBE_HOME`, else
`./data/` if it exists in the current directory (repo-local mode for remote /
mobile sessions), else `~/.scribe/`. `<skill-dir>` means the directory
containing this SKILL.md.

## Procedure

1. Run `python3 <skill-dir>/scripts/due_notes.py` → JSONL per due note:
   `{"id","title","next_review","interval_days"}`.
   If empty, tell the user nothing is due and stop.
2. For each due note, one at a time:
   a. Read `$SCRIBE_HOME/notes/<id>.md` yourself, but do NOT show, quote, or
      paraphrase it to the user before the quiz.
   b. Ask 2–3 questions built from its key takeaways, one per message.
   c. Grade honestly against the note. Name what was right, correct what was
      wrong using the note's content. Do not inflate grades to be polite.
3. Update the note's frontmatter:
   - good recall (most answers substantially right):
     `interval_days = round(interval_days * 2.5)`
   - shaky or failed: `interval_days = 3`
   - `next_review = today + interval_days` (YYYY-MM-DD)
   Leave the body untouched.
4. Finish with one line: how many reviewed, how many solid vs. reset, and the
   nearest next_review date.
