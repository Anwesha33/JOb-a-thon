#!/usr/bin/env bash
#
# One-command launcher: sets up dependencies, starts the FastAPI backend and
# the Vite frontend, and opens the UI in your browser. Ctrl+C stops both.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- .env -----------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  echo "→ Created .env from .env.example."
  echo "  Add your free Adzuna keys (https://developer.adzuna.com/) before searching."
fi

# --- backend --------------------------------------------------------------
echo "→ Setting up backend…"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip >/dev/null
pip install -q -r requirements.txt

echo "→ Starting backend on http://localhost:8000"
uvicorn app.main:app --port 8000 --reload &
BACKEND_PID=$!

# --- frontend -------------------------------------------------------------
echo "→ Setting up frontend…"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install
fi

echo "→ Starting frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

# --- lifecycle ------------------------------------------------------------
cleanup() {
  echo
  echo "→ Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Give the dev servers a moment, then open the UI.
sleep 4
if command -v open >/dev/null 2>&1; then
  open http://localhost:5173 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:5173 || true
fi

echo
echo "JOb-a-thon is running. Press Ctrl+C to stop."
wait
