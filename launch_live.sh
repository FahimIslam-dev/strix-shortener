#!/bin/bash
DIR="/home/fahim/strix-shortener"
cd "$DIR"

# Check if port 8000 is running, if not start it
if ! curl -s -o /dev/null http://localhost:8000/ ; then
    source "$DIR/venv/bin/activate"
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &
    sleep 1.5
fi

# Open in browser
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:8000"
fi
