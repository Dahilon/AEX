#!/bin/bash
# Start AEX backend (FastAPI + Datadog instrumentation)
# Run from repo root.

set -e

cd "$(dirname "$0")/backend"

# Load env vars
if [ -f services/.env ]; then
  export $(grep -v '^#' services/.env | xargs)
else
  echo "⚠️  backend/services/.env not found. Copy backend/services/.env.example to backend/services/.env and fill in secrets."
  exit 1
fi

# Activate virtual environment
if [ -f ../.venv/bin/activate ]; then
  source ../.venv/bin/activate
else
  echo "Creating virtual environment..."
  python3 -m venv ../.venv
  source ../.venv/bin/activate
  pip install -r services/requirements.txt
fi

echo "✅ Starting AEX backend on http://localhost:8000"
echo "   SIGNAL_MODE=${SIGNAL_MODE}"
echo "   MARKET_TICK_INTERVAL_MS=${MARKET_TICK_INTERVAL_MS}"
echo ""

DD_SERVICE=aex DD_ENV=demo \
  ddtrace-run uvicorn backend.services.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info
