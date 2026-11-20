#!/bin/bash
# StrixShort Startup Script by StrixDevs
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"

PORT=${PORT:-8000}
HOST=${HOST:-"0.0.0.0"}

echo "🚀 Starting StrixShort by StrixDevs on http://$HOST:$PORT ..."
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 2
