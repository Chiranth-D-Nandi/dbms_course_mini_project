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

echo "--> Initializing database objects..."
$PYTHON backend/manage.py init_db

echo "--> Seeding database..."
$PYTHON scripts/seed.py

echo "--> Ingesting vector embeddings..."
$PYTHON scripts/ingest_chroma.py

echo "--> Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "======================================================================"
echo "  Setup completed successfully! Run ./scripts/dev.sh to start services."
echo "======================================================================"
