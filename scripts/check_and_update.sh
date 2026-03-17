#!/bin/bash
# check_and_update.sh - called by cron at 3AM weekly.
# Only pulls if there is actually a new commit on origin/main.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Fetch latest remote info
git fetch origin main --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[auto-update] New version found ($REMOTE). Updating..."
    bash "$PROJECT_DIR/scripts/update.sh"
else
    echo "[auto-update] Already up to date ($LOCAL)."
fi