# Local setup; existing databases are preserved.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Setup step failed: $Executable (exit $LASTEXITCODE)" }
}
if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    throw "Created .env. Set MYSQL_ROOT_PASSWORD, then rerun this script."
}
if (-not (Test-Path -LiteralPath ".venv")) {
    Invoke-Checked -Executable "python" -Arguments @("-m", "venv", ".venv")
}
$ProjectPython = ".\.venv\Scripts\python.exe"
Invoke-Checked -Executable $ProjectPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")
Invoke-Checked -Executable $ProjectPython -Arguments @("scripts/configure_env.py")
Invoke-Checked -Executable $ProjectPython -Arguments @("backend/manage.py", "init_db", "--if-empty")
Invoke-Checked -Executable $ProjectPython -Arguments @("scripts/seed.py")
Invoke-Checked -Executable $ProjectPython -Arguments @("scripts/ingest_chroma.py")
Push-Location frontend
try {
    Invoke-Checked -Executable "npm.cmd" -Arguments @("ci", "--no-audit", "--no-fund")
    Invoke-Checked -Executable "npm.cmd" -Arguments @("run", "build")
} finally { Pop-Location }
Write-Host "Setup complete. Run .\scripts\dev.ps1 to start the application."
