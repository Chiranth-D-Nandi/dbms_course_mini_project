# Starts both services and selects free ports automatically.
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe scripts/dev.py
exit $LASTEXITCODE
