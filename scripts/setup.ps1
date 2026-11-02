# Owner: Person B
# scripts/setup.ps1: Complete Local Setup Script for Windows PowerShell
# Verifies environment, initializes virtualenv, provisions MySQL DB via manage.py init_db,
# seeds database, caches offline Chroma embeddings, and builds Next.js frontend.

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Tatkal High-Concurrency Train Booking System - Setup" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Environment check
if (-not (Test-Path ".env")) {
    Write-Host "--> Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "--> Please verify your MySQL credentials in .env before continuing." -ForegroundColor Yellow
}

# 2. Virtual environment check
if (-not (Test-Path ".venv")) {
    Write-Host "--> Creating Python virtual environment in .venv..." -ForegroundColor Green
    python -m venv .venv
}

$PYTHON = ".\.venv\Scripts\python.exe"
$PIP = ".\.venv\Scripts\pip.exe"

# 3. Python package installation
Write-Host "--> Installing pinned backend dependencies from requirements.txt..." -ForegroundColor Green
& $PIP install -r requirements.txt

# 4. Database Initialization
Write-Host "--> Running database DDL and objects initialization via manage.py init_db..." -ForegroundColor Green
& $PYTHON backend\manage.py init_db

# 5. Seed realistic data
Write-Host "--> Seeding realistic stations, trains, runs, and demo users..." -ForegroundColor Green
& $PYTHON scripts\seed.py

# 6. Ingest ChromaDB vectors
Write-Host "--> Ingesting offline ChromaDB embeddings and train descriptions..." -ForegroundColor Green
& $PYTHON scripts\ingest_chroma.py

# 7. Frontend installation and build
Write-Host "--> Installing frontend dependencies and compiling Next.js 14..." -ForegroundColor Green
Push-Location frontend
npm install
npm run build
Pop-Location

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  Setup completed successfully! Run .\scripts\dev.ps1 to start services." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
