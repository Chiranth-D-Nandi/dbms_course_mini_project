#!/usr/bin/env bash
# Owner: Person A
# Handoff script for Linux/macOS
# Distributes repository files into handoff/person_a and handoff/person_b according to OWNERSHIP.csv

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_ROOT"

OWNERSHIP_FILE="$WORKSPACE_ROOT/OWNERSHIP.csv"
if [ ! -f "$OWNERSHIP_FILE" ]; then
    echo "ERROR: OWNERSHIP.csv not found at $OWNERSHIP_FILE" >&2
    exit 1
fi

echo "==> Verifying OWNERSHIP.csv and generating handoff packages..."

HANDOFF_DIR="$WORKSPACE_ROOT/handoff"
HANDOFF_A="$HANDOFF_DIR/person_a"
HANDOFF_B="$HANDOFF_DIR/person_b"

rm -rf "$HANDOFF_DIR"
mkdir -p "$HANDOFF_A" "$HANDOFF_B"

# PowerShell handoff does the canonical processing on Windows,
# this bash script provides parity on Linux/macOS.
python3 - << 'EOF'
import os
import csv
import shutil

root = os.getcwd()
ownership_file = os.path.join(root, "OWNERSHIP.csv")
rules = []
with open(ownership_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rules.append((row["path_glob"].replace("\\", "/"), row["owner"].strip()))

ignore_dirs = {".git", ".venv", "venv", "node_modules", ".next", "__pycache__", "models", "chroma_data", "handoff", ".pytest_cache", "playwright-report", "test-results"}
ignore_files = {".env", ".DS_Store", "Thumbs.db"}

def get_owner(rel_path):
    norm = rel_path.replace("\\", "/")
    matches = []
    for glob, owner in rules:
        if glob.endswith("/**"):
            prefix = glob[:-3]
            if norm == prefix or norm.startswith(prefix + "/"):
                matches.append(owner)
        elif norm == glob:
            matches.append(owner)
    if not matches:
        return "UNOWNED"
    return matches[0]

handoff_a = os.path.join(root, "handoff", "person_a")
handoff_b = os.path.join(root, "handoff", "person_b")

files_a, lines_a = 0, 0
files_b, lines_b = 0, 0
unowned = []

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
    for filename in filenames:
        if filename in ignore_files:
            continue
        full_path = os.path.join(dirpath, filename)
        rel_path = os.path.relpath(full_path, root).replace("\\", "/")
        
        owner = get_owner(rel_path)
        if owner == "UNOWNED":
            unowned.append(rel_path)
            continue
            
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            line_count = sum(1 for _ in f)
            
        if owner == "Person A":
            dest = os.path.join(handoff_a, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(full_path, dest)
            files_a += 1
            lines_a += line_count
        elif owner == "Person B":
            dest = os.path.join(handoff_b, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(full_path, dest)
            files_b += 1
            lines_b += line_count

if unowned:
    print(f"ERROR: Unowned files detected:\n" + "\n".join(unowned))
    exit(1)

total = lines_a + lines_b
pct_a = (lines_a / total * 100) if total else 0
pct_b = (lines_b / total * 100) if total else 0

print(f"Handoff Complete!")
print(f"Person A: {files_a} files, {lines_a} lines ({pct_a:.1f}%)")
print(f"Person B: {files_b} files, {lines_b} lines ({pct_b:.1f}%)")
EOF
