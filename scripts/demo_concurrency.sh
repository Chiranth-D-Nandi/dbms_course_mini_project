#!/usr/bin/env bash
# Owner: Person B
# scripts/demo_concurrency.sh: High-Concurrency Stress Test Demo
set -e

echo "======================================================================"
echo "  DEMO: High-Concurrency Stress Test (Zero Double-Booking Verification)"
echo "======================================================================"

./.venv/bin/pytest backend/tests/test_concurrency.py -v -s
