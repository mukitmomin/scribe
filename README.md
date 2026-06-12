# Scribe

Papers in, understanding out, in your terminal. Scribe is a Claude Code plugin
that scans arXiv, Hacker News, and Hugging Face for papers matching your
interests, teaches them to you interactively, quizzes you with spaced
repetition, and drafts blog posts from your notes — all without leaving the
command line.

## Install (60 seconds)

In Claude Code:

```
/plugin marketplace add mukitmomin/scribe
/plugin install scribe@scribe
```

On first run, Scribe creates `~/.scribe/interests.md` from a template and asks
you to edit it — list your themes, keywords, depth level, and an avoid-list.
Everything else is automatic.

## Commands

| Command | What it does | Example |
| --- | --- | --- |
| `/scribe:scan` | Finds the week's papers matching your interests, scores them, and files the best into your inbox | `/scribe:scan` |
| `/scribe:learn` | Teaches a paper section by section, then saves a note for review | `/scribe:learn 1706.03762` |
| `/scribe:review` | Quizzes you on notes that are due, spaced-repetition style | `/scribe:review` |
| `/scribe:draft` | Turns one of your notes into a first-person blog draft | `/scribe:draft 1706.03762` |

`/scribe:learn` and `/scribe:draft` take an optional arXiv id; with no id,
`/scribe:learn` picks the highest-scoring paper in your inbox.

## Other agents

The skills are written for any coding agent, not just Claude. Point your agent
at the relevant `SKILL.md` and it will follow the same workflow:

- Scan: `skills/scout/SKILL.md`
- Learn: `skills/tutor/SKILL.md`
- Review: `skills/reviewer/SKILL.md`

## Bare scripts (no agent)

The deterministic plumbing runs on its own — Python 3.11, standard library
only, no installs:

```bash
# Find candidate papers for your queries (JSONL to stdout)
python3 skills/scout/scripts/fetch_candidates.py --queries "LLM agents" "RAG" --max 40

# Fetch a paper's section map, then one section
python3 skills/tutor/scripts/fetch_paper.py --id 1706.03762
python3 skills/tutor/scripts/fetch_paper.py --id 1706.03762 --section 3

# List notes that are due for review (JSONL)
python3 skills/reviewer/scripts/due_notes.py
```

## Design

Scribe splits the work cleanly:

- **Scripts do the plumbing.** Deterministic Python fetches, parses, dedupes,
  and truncates — so the model only ever sees compact JSONL or clean text.
- **The model does the judgment.** Relevance scoring, teaching, quizzing, and
  drafting — the parts that actually need reasoning.
- **Files are the database.** No server, no DB. Your data lives as Markdown and
  JSON under `~/.scribe/`, readable and editable by hand.

## State (`~/.scribe/`)

The state dir is resolved in order: `$SCRIBE_HOME` if set, else `./data/` if it
exists in the current directory (repo-local mode — see below), else `~/.scribe/`.
Scripts create it on first run.

```
~/.scribe/
├── interests.md          # you edit this: themes, keywords, depth, avoid-list
├── seen.json             # arxiv ids already scanned, with dates
├── digests/YYYY-MM-DD.md # the ranked table from each scan
├── inbox/<id>.md         # papers worth learning, waiting for you
├── notes/<id>.md         # what you learned, with review schedule
└── drafts/<id>.md        # blog drafts generated from notes
```

## Headless / scheduled scans

`/scribe:scan` runs fine without an interactive session, so you can have a fresh
digest waiting each morning. A daily cron entry (sourcing an env file that holds
`SCRIBE_HOME` and, optionally, `SLACK_WEBHOOK_URL`):

```cron
0 6 * * *  . $HOME/scribe.env && claude -p "/scribe:scan" >> $HOME/scan.log 2>&1
```

For a one-off recurring run inside an interactive session you can use `/loop`,
but that lasts only as long as the session — cron is the durable option.

### Slack notifications

Set `SLACK_WEBHOOK_URL` (a Slack [incoming webhook](https://api.slack.com/messaging/webhooks))
and each scan posts its top 5 papers to that channel as plain ranked lines.
Unset, scans run exactly as before — the notification step is a silent no-op.

### Repo-local state & the mobile workflow

If the current directory contains a `./data/` folder, Scribe stores state there
instead of `~/.scribe/`. When that folder is a git repo, `/scribe:scan` and
`/scribe:learn` commit and push their changes automatically. This enables a
phone-first loop:

1. A scheduled scan (e.g. on a homelab box) writes the digest into a private
   `scribe-data` repo and pushes it, then pings Slack.
2. You read the digest from Slack or the GitHub mobile app over coffee.
3. From the **Claude mobile app**, open the repo and run `/scribe:learn <id>` —
   it reads and writes `./data/`, then pushes your note back.

So discovery is automated and learning happens from your phone, with the repo
as the single source of truth.

## License

MIT — see [LICENSE](LICENSE).
