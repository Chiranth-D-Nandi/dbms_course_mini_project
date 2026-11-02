# Owner: Person B
# scripts/preflight.ps1: Pre-Flight Environment & Health Diagnostic
# Checks Python, Node, MySQL connectivity, event scheduler, ChromaDB offline cache, and DB tables.

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  System Pre-Flight Health & Diagnostic Check" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$allPass = $true

# 1. Python Check
try {
    $pyVer = & .\.venv\Scripts\python.exe --version
    Write-Host "[OK] Python Virtual Environment: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python virtual environment (.venv) not found or broken." -ForegroundColor Red
    $allPass = $false
}

# 2. Node Check
try {
    $nodeVer = & node --version
    Write-Host "[OK] Node.js Environment: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Node.js not detected on PATH." -ForegroundColor Red
    $allPass = $false
}

# 3. MySQL & Event Scheduler Diagnostic
try {
    $dbCheck = & .\.venv\Scripts\python.exe scripts\preflight_check.py
    if ($dbCheck -match "TABLE_COUNT:(\d+)\|EVENT_SCHEDULER:(\w+)") {
        $tblCount = $Matches[1]
        $evSched = $Matches[2]
        Write-Host "[OK] MySQL 8.0 Connected: Found $tblCount tables in tatkal_db." -ForegroundColor Green
        if ($evSched -eq "ON") {
            Write-Host "[OK] MySQL Event Scheduler: ON (Background hold release active)" -ForegroundColor Green
        } else {
            Write-Host "[WARN] MySQL Event Scheduler: $evSched (Run 'SET GLOBAL event_scheduler=ON')" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[FAIL] MySQL connectivity failed: $_" -ForegroundColor Red
    $allPass = $false
}

# 4. ChromaDB Offline Model Check
$modelDir = "models\all-MiniLM-L6-v2"
if ((Test-Path $modelDir) -and (Get-ChildItem $modelDir).Count -gt 0) {
    Write-Host "[OK] Offline Embedding Model: Cached at $modelDir" -ForegroundColor Green
} else {
    Write-Host "[WARN] Offline model not found. Run 'python scripts/ingest_chroma.py'." -ForegroundColor Yellow
}

# 5. ChromaDB Vector Database Check
$chromaDir = "chroma_data"
if (Test-Path $chromaDir) {
    Write-Host "[OK] ChromaDB Vector Database: Initialized at $chromaDir" -ForegroundColor Green
} else {
    Write-Host "[WARN] ChromaDB directory not found. Run 'python scripts/ingest_chroma.py'." -ForegroundColor Yellow
}

Write-Host "======================================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host "  PREFLIGHT STATUS: ALL CRITICAL SYSTEMS HEALTHY & READY!" -ForegroundColor Green
} else {
    Write-Host "  PREFLIGHT STATUS: ISSUES DETECTED. PLEASE RESOLVE ABOVE ERRORS." -ForegroundColor Red
}
Write-Host "======================================================================" -ForegroundColor Cyan
