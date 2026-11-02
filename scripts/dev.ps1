# Owner: Person B
# scripts/dev.ps1: Development Server Launcher for Windows
# Launches Django REST API (port 8000) and Next.js 14 Frontend (port 3000) concurrently.

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Starting Tatkal High-Concurrency Full-Stack Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$PYTHON = ".\.venv\Scripts\python.exe"

# Start Django Backend in a separate background job or window
Write-Host "--> Launching Django Backend at http://127.0.0.1:8000/api/..." -ForegroundColor Green
$backendJob = Start-Process -FilePath $PYTHON -ArgumentList "backend\manage.py runserver 127.0.0.1:8000" -PassThru

# Start Next.js Frontend
Write-Host "--> Launching Next.js Frontend at http://localhost:3000/..." -ForegroundColor Green
Push-Location frontend
try {
    npm run dev
} finally {
    Pop-Location
    if ($backendJob -and -not $backendJob.HasExited) {
        Write-Host "--> Terminating backend service..." -ForegroundColor Yellow
        Stop-Process -Id $backendJob.Id -Force
    }
}
