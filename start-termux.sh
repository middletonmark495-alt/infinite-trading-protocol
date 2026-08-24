#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
HOST="127.0.0.1"
PORT="${PORT:-8000}"
URL="http://${HOST}:${PORT}"

echo "Infinite Trading Intelligence"
echo "Mode: READ-ONLY"
echo "Execution: LOCKED"
echo "API: $URL"
echo "Docs: $URL/docs"
echo "Control Center: $ROOT/apps/control-center/index.html"

command -v python >/dev/null 2>&1 || { echo 'Python is required. Run: pkg install python'; exit 1; }
python -c 'import fastapi,uvicorn' >/dev/null 2>&1 || { echo 'Missing FastAPI/Uvicorn. Run: python -m pip install -r requirements-mvp.txt'; exit 1; }

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

if curl -fsS "$URL/health" >/dev/null 2>&1; then
  echo "API: ALREADY RUNNING"
  echo "Open: $URL/docs"
  exit 0
fi

exec python apps/api/main.py
