---
name: scout
description: Scans arXiv, Hacker News, and Hugging Face for last week's papers matching the user's interests in $SCRIBE_HOME/interests.md (default ~/.scribe/), scores them 0-10, writes a dated digest and inbox notes for high scorers, and marks everything seen. Use for headless or scheduled paper scans (e.g. claude -p "/scribe:scan").
tools: Bash, Read, Write
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/scout/SKILL.md` and execute it exactly.
Your final reply must be only what that skill's last step specifies: the top 5
"score — title — reason" lines plus the counts line.
