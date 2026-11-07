#!/usr/bin/env bash
# Owner: Person B
# scripts/setup.sh: Complete Local Setup Script for Linux / macOS
set -e

echo "======================================================================"
echo "  Tatkal High-Concurrency Train Booking System - Setup"
echo "======================================================================"

if [ ! -f ".env" ]; then
    echo "--> Creating .env from .env.example..."
    cp .env.example .env
fi

if [ ! -d ".venv" ]; then
    echo "--> Creating Python virtual environment in .venv..."
    python3 -m venv .venv
fi

PYTHON="./.venv/bin/python"
PIP="./.venv/bin/pip"

echo "--> Installing pinned backend dependencies..."
$PIP install -r requirements.txt

$PYTHON scripts/configure_env.py
echo "--> Initializing database objects..."
$PYTHON backend/manage.py init_db --if-empty

echo "--> Seeding database..."
$PYTHON scripts/seed.py

echo "--> Ingesting vector embeddings..."
$PYTHON scripts/ingest_chroma.py

echo "--> Building frontend..."
cd frontend
npm ci --no-audit --no-fund
npm run build
cd ..

echo "======================================================================"
echo "  Setup completed successfully! Run ./scripts/dev.sh to start services."
echo "======================================================================"
