#!/bin/sh
# BIDPILOT_MODE=api serves the agent surface (REST + MCP); anything else keeps
# the public Streamlit app as the default process.
set -eu
PORT="${PORT:-8080}"
if [ "${BIDPILOT_MODE:-}" = "api" ]; then
  exec .venv/bin/uvicorn bidpilot.api_server:app --host 0.0.0.0 --port "$PORT"
fi
exec .venv/bin/streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port="$PORT" \
  --server.headless=true \
  --browser.gatherUsageStats=false
