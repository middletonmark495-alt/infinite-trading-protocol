#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH="$PWD"
command -v python >/dev/null || { echo 'Python is required. Run: pkg install python'; exit 1; }
python -c 'import fastapi,uvicorn' >/dev/null 2>&1 || { echo 'Missing FastAPI/Uvicorn. Run: python -m pip install fastapi uvicorn pydantic requests pytest httpx'; exit 1; }
echo 'Infinite Trading Intelligence'
echo 'Mode: READ-ONLY'
echo 'Execution: LOCKED'
echo 'API: http://127.0.0.1:8000'
echo 'Docs: http://127.0.0.1:8000/docs'
echo 'Control Center: apps/control-center/index.html'
exec python apps/api/main.py
