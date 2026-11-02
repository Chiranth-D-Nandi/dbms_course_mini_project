#!/usr/bin/env bash
# Owner: Person B
# scripts/preflight.sh: Pre-Flight Environment & Health Diagnostic
set -e

echo "======================================================================"
echo "  System Pre-Flight Health & Diagnostic Check"
echo "======================================================================"

python3 --version
node --version

./.venv/bin/python scripts/preflight_check.py

echo "======================================================================"
echo "  PREFLIGHT STATUS: ALL CRITICAL SYSTEMS HEALTHY & READY!"
echo "======================================================================"
