#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
PORT="${PORT:-8000}"
URL="http://127.0.0.1:$PORT"

if [ ! -d "$FRONTEND_DIR/dist" ]; then
  echo "Build frontend mancante, la genero..."
  (cd "$FRONTEND_DIR" && npm install && npm run build)
fi

(cd "$BACKEND_DIR" && uv sync)

(cd "$BACKEND_DIR" && uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT") &
BACKEND_PID=$!

trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

echo "Attendo che il backend sia pronto su $URL..."
for _ in $(seq 1 50); do
  if curl -sf "$URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  open "$URL" &
else
  echo "Apri il browser su $URL"
fi

wait "$BACKEND_PID"
