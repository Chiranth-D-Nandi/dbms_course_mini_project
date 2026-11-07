# Verifies expiration through payment and the scheduler procedure in an isolated database.
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_regressions.py -k expired_seats -v -s
exit $LASTEXITCODE
