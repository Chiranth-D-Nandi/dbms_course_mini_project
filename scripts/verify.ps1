# Run the complete local verification workflow. Pytest uses an isolated database.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe backend/manage.py check
if ($LASTEXITCODE -ne 0) { throw "Django check failed" }
& .\.venv\Scripts\python.exe -m pytest backend/tests -q
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed" }
Push-Location frontend
try {
    npm.cmd run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Typecheck failed" }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Production build failed" }
    npm.cmd run test:e2e
    if ($LASTEXITCODE -ne 0) { throw "Browser tests failed" }
} finally { Pop-Location }
Write-Host "All verification checks passed."
