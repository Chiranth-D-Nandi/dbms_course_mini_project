#!/usr/bin/env bash
# Owner: Person B
# scripts/demo_reset.sh: Reset Database State to Clean Seeded Baseline
set -e

echo "======================================================================"
echo "  DEMO: Reset Database to Clean Seeded State"
echo "======================================================================"

PYTHON="./.venv/bin/python"

echo "--> Running init_db..."
$PYTHON backend/manage.py init_db

echo "--> Reseeding data..."
$PYTHON scripts/seed.py

echo "  [OK] Database successfully reset and seeded!"
