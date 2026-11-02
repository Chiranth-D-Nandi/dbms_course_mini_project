# Owner: Person B
# scripts/demo_reset.ps1: Reset Database State to Clean Seeded Baseline
# Re-runs manage.py init_db and scripts\seed.py.

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  DEMO: Reset Database to Clean Seeded State" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$PYTHON = ".\.venv\Scripts\python.exe"

Write-Host "--> Running init_db..." -ForegroundColor Green
& $PYTHON backend\manage.py init_db

Write-Host "--> Reseeding data..." -ForegroundColor Green
& $PYTHON scripts\seed.py

Write-Host "  [OK] Database successfully reset and seeded!" -ForegroundColor Green
