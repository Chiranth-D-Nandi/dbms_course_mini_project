# Owner: Person B
# scripts/demo_tatkal_window.ps1: Demonstrate Tatkal Window Opening Logic
# Queries seat map tatkal status calculation for both AC and Non-AC classes.

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  DEMO: Tatkal Window Opening Logic Verification" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$PYTHON = ".\.venv\Scripts\python.exe"

& $PYTHON -c "
import sys
sys.path.insert(0, 'backend')
from booking_engine.seat_views import get_tatkal_window_info
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
print(f'Target Journey Date: {tomorrow}')
print('\n[1] AC Class (3A) Tatkal Window Info:')
print(get_tatkal_window_info(tomorrow, '3A'))

print('\n[2] Non-AC Class (SL) Tatkal Window Info:')
print(get_tatkal_window_info(tomorrow, 'SL'))
"
