#!/usr/bin/env bash
# Owner: Person B
# scripts/dev.sh: Development Server Launcher for Linux / macOS

echo "======================================================================"
echo "  Starting Tatkal High-Concurrency Full-Stack Services"
echo "======================================================================"

PYTHON="./.venv/bin/python"

# Trap interrupt to clean up child jobs
cleanup() {
    echo "--> Terminating services..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "--> Launching Django Backend at http://127.0.0.1:8000/api/..."
$PYTHON backend/manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!

echo "--> Launching Next.js Frontend at http://localhost:3000/..."
cd frontend
npm run dev
