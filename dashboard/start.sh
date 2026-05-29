#!/usr/bin/env bash
# Starts the FastAPI backend and Vite frontend in parallel.
# Usage: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"
FRONTEND="$SCRIPT_DIR/frontend"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Balance Transfer Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install Python deps if venv doesn't exist
if [ ! -d "$BACKEND/.venv" ]; then
  echo "► Setting up Python virtual environment…"
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
  echo "✓ Python deps installed"
fi

# Install Node deps if node_modules doesn't exist
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "► Installing frontend dependencies…"
  cd "$FRONTEND" && npm install --silent
  echo "✓ Node deps installed"
fi

# Start backend
echo "► Starting backend on http://localhost:8000"
cd "$BACKEND" && "$BACKEND/.venv/bin/uvicorn" main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "► Starting frontend on http://localhost:5173"
cd "$FRONTEND" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ Dashboard running at http://localhost:5173"
echo "  API docs at         http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
