#!/usr/bin/env bash
# ── ITP Dashboard launcher ────────────────────────────────────────────────────
# Usage: ./launch.sh
# Opens the dashboard at http://localhost:8000

set -e
cd "$(dirname "$0")"

# Load .env if present
if [ -f .env ]; then
  echo "Loading .env…"
  set -o allexport
  # shellcheck source=/dev/null
  source .env
  set +o allexport
else
  echo "Warning: .env not found. Copy .env.example to .env and fill in your values."
fi

# Open browser in background (works on macOS and Linux)
(
  sleep 1
  if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:8000"
  elif command -v open &>/dev/null; then
    open "http://localhost:8000"
  fi
) &

python3 src/web/server.py
