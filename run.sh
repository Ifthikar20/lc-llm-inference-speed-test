#!/usr/bin/env bash
#
# One-shot launcher: sets up Python, ensures Ollama is running with the model
# pulled, then starts the FastAPI app. Re-runnable and safe to run repeatedly.
#
# Usage:
#   ./run.sh                      # defaults: model=deepseek-r1:14b, port=8000
#   LLM_MODEL=qwen2.5:14b ./run.sh
#   PORT=9000 ./run.sh
#
set -euo pipefail

MODEL="${LLM_MODEL:-deepseek-r1:14b}"
PORT="${PORT:-8000}"
OLLAMA_URL="${LLM_OLLAMA_BASE_URL:-http://localhost:11434}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

c_blue=$'\033[1;34m'; c_green=$'\033[1;32m'; c_red=$'\033[1;31m'; c_off=$'\033[0m'
say()  { printf '%s==>%s %s\n' "$c_blue"  "$c_off" "$*"; }
ok()   { printf '%s ok%s %s\n'  "$c_green" "$c_off" "$*"; }
die()  { printf '%serr%s %s\n'  "$c_red"   "$c_off" "$*" >&2; exit 1; }

# 1. Ollama installed?
command -v ollama >/dev/null 2>&1 || die \
  "Ollama not found. Install it from https://ollama.com/download then re-run."
ok "Ollama is installed."

# 2. Ollama server reachable? Start it in the background if not.
if ! curl -fsS "$OLLAMA_URL/api/version" >/dev/null 2>&1; then
  say "Starting Ollama server..."
  ollama serve >/tmp/ollama.log 2>&1 &
  for _ in $(seq 1 30); do
    curl -fsS "$OLLAMA_URL/api/version" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -fsS "$OLLAMA_URL/api/version" >/dev/null 2>&1 \
    || die "Ollama server did not come up. See /tmp/ollama.log"
fi
ok "Ollama server is running at $OLLAMA_URL"

# 3. Model present? Pull it if missing (one-time download).
if ! ollama list 2>/dev/null | grep -q "^${MODEL%%:*}"; then
  say "Pulling model '$MODEL' (one-time download, can be several GB)..."
  ollama pull "$MODEL"
fi
ok "Model '$MODEL' is available."

# 4. Python virtualenv + deps.
if [ ! -d .venv ]; then
  say "Creating virtualenv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
say "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Dependencies installed."

# 5. Launch the API (export config so the app uses the same model/URL).
export LLM_MODEL="$MODEL"
export LLM_OLLAMA_BASE_URL="$OLLAMA_URL"
say "Starting app on http://localhost:$PORT  (UI at /, docs at /docs)"
echo
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
