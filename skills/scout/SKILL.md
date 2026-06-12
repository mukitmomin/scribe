---
name: scout
description: Scan arXiv, Hacker News, and Hugging Face for last week's papers matching the user's interests, score them, write a digest, and file the best into the inbox. Use for /scribe:scan or any "find me new papers" request.
---

# Scout

State lives under the state dir, resolved in order: `$SCRIBE_HOME`, else
`./data/` if it exists in the current directory (repo-local mode for remote /
mobile sessions), else `~/.scribe/`. Scripts create it and seed `interests.md`
on first run. `<skill-dir>` below means the directory containing this SKILL.md.

## Procedure

1. Read `$SCRIBE_HOME/interests.md`. If it does not exist yet, run step 3 once
   (the script seeds it), then tell the user to edit it and STOP — do not scan
   against the template defaults.
2. Derive at most 5 short arXiv query strings from the themes and keywords
   (e.g. "LLM agents", "retrieval augmented generation" — plain phrases, no
   boolean operators).
3. Run:
   `python3 <skill-dir>/scripts/fetch_candidates.py --queries "q1" "q2" ... --max 40`
   Stdout is JSONL, one paper per line:
   `{"id","title","abstract","categories","published","signals":{"hn_points","hn_comments","hf_upvotes","matched_queries"}}`
   Source failures are warned on stderr; proceed with whatever was fetched.
4. Score every candidate 0–10 in ONE pass — no fetching papers, no browsing.
   Weigh: relevance to the themes (dominant), keyword matches, signal strength
   (hn_points, hn_comments, hf_upvotes, multiple matched_queries), and subtract
   sharply for avoid-list matches. Produce ONLY this JSON, nothing else:
   `[{"id": "...", "score": N, "reason": "<=15 words"}]`
5. Write `$SCRIBE_HOME/digests/<YYYY-MM-DD>.md`: a markdown table sorted by
   score descending — columns: Score | Title | Reason | Link
   (link = `https://arxiv.org/abs/<id>`).
6. For each paper with score >= 7, write `$SCRIBE_HOME/inbox/<id>.md`:

   ```
   ---
   title: <title>
   score: <score>
   sources: [<arxiv and/or hn, hf — whichever signals were nonzero>]
   status: inbox
   ---
   <abstract>
   ```

7. Run `python3 <skill-dir>/scripts/mark_seen.py --ids <id1> <id2> ...` with
   ALL ids fetched in step 3, not just the inboxed ones.
8. Run `python3 <skill-dir>/scripts/sync.py --label scan` to commit and push
   the state dir when it is a git repo (no-op otherwise).
9. Run `python3 <skill-dir>/scripts/notify.py` to post the top 5 to Slack
   (no-op when `$SLACK_WEBHOOK_URL` is unset). This is the final script step.
10. Reply with exactly: the top 5 as "score — title — reason" lines, then one
    line of counts (fetched N, inboxed M, digest path). Nothing more.
