#!/bin/bash
# update.sh - pull latest code from GitHub and restart the service.
# Called by the updater API endpoint and by the weekly cron job.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[update] Pulling latest code..."
git fetch origin main
git reset --hard origin/main

echo "[update] Rebooting Pi..."
reboot