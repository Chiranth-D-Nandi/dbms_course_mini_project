#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./.venv/bin/python -m pytest backend/tests/test_regressions.py -k expired_seats -v -s
