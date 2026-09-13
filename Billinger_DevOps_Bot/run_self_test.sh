#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PYTHON_BIN=$(command -v python3 || command -v python || true)
exec "$PYTHON_BIN" tests/run_tests.py
