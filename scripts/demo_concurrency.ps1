# Owner: Person B
# scripts/demo_concurrency.ps1: High-Concurrency Stress Test Demo
# Demonstrates 16 concurrent threads hammering the same seats simultaneously with ZERO double-booking.

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  DEMO: High-Concurrency Stress Test (Zero Double-Booking Verification)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$PYTHON = ".\.venv\Scripts\python.exe"
$PYTEST = ".\.venv\Scripts\pytest.exe"

& $PYTEST backend\tests\test_concurrency.py -v -s
