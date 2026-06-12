#!/usr/bin/env bash
# Pull latest plugin code from origin/main before the nightly scan.
# Exit 0 always — a failure falls back to the existing version.
set -euo pipefail

PLUGIN_DIR="${SCRIBE_PLUGIN_DIR:-$HOME/scribe}"

git -C "$PLUGIN_DIR" fetch origin main --quiet

LOCAL=$(git -C "$PLUGIN_DIR" rev-parse HEAD)
REMOTE=$(git -C "$PLUGIN_DIR" rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "scribe-deploy: up to date (${LOCAL:0:7})"
  exit 0
fi

git -C "$PLUGIN_DIR" pull --ff-only origin main
SHORT_NEW="${REMOTE:0:7}"
echo "scribe-deploy: updated ${LOCAL:0:7} -> $SHORT_NEW"

if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  curl -s -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"scribe: deployed \`$SHORT_NEW\` on $(hostname)\"}" || true
fi
