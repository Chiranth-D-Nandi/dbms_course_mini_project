# Owner: Person A
# Handoff script for Windows PowerShell
# Distributes repository files into handoff/person_a and handoff/person_b according to OWNERSHIP.csv

$ErrorActionPreference = "Stop"
$WorkspaceRoot = (Resolve-Path "$PSScriptRoot/..").Path
Set-Location $WorkspaceRoot

$OwnershipFile = Join-Path $WorkspaceRoot "OWNERSHIP.csv"
if (-not (Test-Path $OwnershipFile)) {
    Write-Error "OWNERSHIP.csv not found at $OwnershipFile"
}

Write-Host "==> Verifying OWNERSHIP.csv rules..." -ForegroundColor Cyan
$Rules = Import-Csv $OwnershipFile

# Define directories to ignore completely
$IgnoreDirs = @(
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "__pycache__",
    "models",
    "chroma_data",
    "handoff",
    ".pytest_cache",
    "playwright-report",
    "test-results"
)

# Define exact file names to ignore
$IgnoreFiles = @(
    ".env",
    ".DS_Store",
    "Thumbs.db"
)

# Helper function to match a file against globs
function Get-FileOwner {
    param([string]$RelativePath)

    # Normalize slashes
    $norm = $RelativePath.Replace("\", "/")

    $matchedOwners = [System.Collections.Generic.List[string]]::new()
    foreach ($rule in $Rules) {
        $glob = $rule.path_glob.Replace("\", "/")
        if ($glob.EndsWith("/**")) {
            $prefix = $glob.Substring(0, $glob.Length - 3)
            if ($norm -eq $prefix -or $norm.StartsWith($prefix + "/")) {
                $matchedOwners.Add($rule.owner)
            }
        } elseif ($norm -eq $glob) {
            $matchedOwners.Add($rule.owner)
        }
    }

    if ($matchedOwners.Count -eq 0) {
        return "UNOWNED"
    }
    if ($matchedOwners.Count -gt 1) {
        # Check if identical
        $first = $matchedOwners[0]
        foreach ($o in $matchedOwners) {
            if ($o -ne $first) { return "CONFLICT" }
        }
        return $first
    }
    return $matchedOwners[0]
}

# Collect all files in workspace
$AllFiles = Get-ChildItem -Path $WorkspaceRoot -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($WorkspaceRoot.Length + 1).Replace("\", "/")
    $parts = $rel.Split("/")
    $skip = $false
    foreach ($part in $parts) {
        if ($IgnoreDirs -contains $part) {
            $skip = $true
            break
        }
    }
    if ($IgnoreFiles -contains $_.Name) {
        $skip = $true
    }
    -not $skip
}

# Clean and recreate handoff folders
$HandoffDir = Join-Path $WorkspaceRoot "handoff"
$HandoffA = Join-Path $HandoffDir "person_a"
$HandoffB = Join-Path $HandoffDir "person_b"

if (Test-Path $HandoffDir) {
    Remove-Item -Recurse -Force $HandoffDir
}
New-Item -ItemType Directory -Path $HandoffA -Force | Out-Null
New-Item -ItemType Directory -Path $HandoffB -Force | Out-Null

$FilesA = 0
$LinesA = 0
$FilesB = 0
$LinesB = 0
$Unowned = @()
$Conflicts = @()

foreach ($file in $AllFiles) {
    $rel = $file.FullName.Substring($WorkspaceRoot.Length + 1)
    $owner = Get-FileOwner -RelativePath $rel

    if ($owner -eq "UNOWNED") {
        $Unowned += $rel
    } elseif ($owner -eq "CONFLICT") {
        $Conflicts += $rel
    } elseif ($owner -eq "Person A") {
        $dest = Join-Path $HandoffA $rel
        $parent = Split-Path -Parent $dest
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item -Path $file.FullName -Destination $dest -Force
        $FilesA++
        try {
            $LinesA += (Get-Content $file.FullName -ErrorAction SilentlyContinue | Measure-Object).Count
        } catch {}
    } elseif ($owner -eq "Person B") {
        $dest = Join-Path $HandoffB $rel
        $parent = Split-Path -Parent $dest
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item -Path $file.FullName -Destination $dest -Force
        $FilesB++
        try {
            $LinesB += (Get-Content $file.FullName -ErrorAction SilentlyContinue | Measure-Object).Count
        } catch {}
    }
}

if ($Unowned.Count -gt 0) {
    Write-Error "ERROR: Found unowned files in repository:`n$($Unowned -join "`n")"
}
if ($Conflicts.Count -gt 0) {
    Write-Error "ERROR: Found files with conflicting ownership rules:`n$($Conflicts -join "`n")"
}

# Copy HOW_TO_COMMIT.md from COMMIT_PLAN.md sections
$CommitPlanPath = Join-Path $WorkspaceRoot "COMMIT_PLAN.md"
$CommitPlan = ""
if (Test-Path $CommitPlanPath) {
    $CommitPlan = Get-Content $CommitPlanPath -Raw
}

# Generate Person B HOW_TO_COMMIT.md
$HowToB = @"
# Person B Handoff & Commit Guide (Jashruth K A)

Welcome to the Person B handoff package! This directory contains all files owned by Person B.

## Instructions to Commit & Push Under Your Git Identity

1. Copy all contents of this folder (\`handoff/person_b/\`) into your local clone of the repository root (\`dbms_course_mini_project/\`).
2. Open your terminal in the repository root.
3. Verify your git credentials:
   \`\`\`bash
   git config user.name "Jashruth K A"
   git config user.email "your_email@example.com"
   \`\`\`
4. Pull the latest commits from Person A:
   \`\`\`bash
   git pull --rebase origin main
   \`\`\`
5. Stage and commit the files phase by phase according to the commit sequence below.
   Use the exact \`git add\` paths and commit messages provided. Do not squash.
6. Push to GitHub:
   \`\`\`bash
   git push origin main
   \`\`\`

---

## Detailed Step-by-Step Commit Sequence for Person B

Refer to the Person B section of COMMIT_PLAN.md for the full structured plan.
"@

Set-Content -Path (Join-Path $HandoffB "HOW_TO_COMMIT.md") -Value $HowToB -Encoding UTF8

# Generate Person A HOW_TO_COMMIT.md
$HowToA = @"
# Person A Commit Record (Chiranth D Nandi)

This folder contains a mirror of all tracked files owned by Person A.
All Person A files are progressively committed and pushed directly to origin main during development.
See COMMIT_PLAN.md for the record of commits executed.
"@
Set-Content -Path (Join-Path $HandoffA "HOW_TO_COMMIT.md") -Value $HowToA -Encoding UTF8

Write-Host "==> Handoff Package Generated Successfully!" -ForegroundColor Green
Write-Host "--------------------------------------------------------" -ForegroundColor Yellow
Write-Host ("Person A (Chiranth D Nandi) : {0,5} files | {1,8} lines" -f $FilesA, $LinesA)
Write-Host ("Person B (Jashruth K A)     : {0,5} files | {1,8} lines" -f $FilesB, $LinesB)
$TotalLines = $LinesA + $LinesB
if ($TotalLines -gt 0) {
    $pctA = [math]::Round(($LinesA / $TotalLines) * 100, 1)
    $pctB = [math]::Round(($LinesB / $TotalLines) * 100, 1)
    Write-Host ("Balance Split Ratio        : {0}% A / {1}% B" -f $pctA, $pctB)
}
Write-Host "--------------------------------------------------------" -ForegroundColor Yellow
