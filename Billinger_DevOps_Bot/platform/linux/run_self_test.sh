#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "[*] Running Billinger Automated Verification Suite..."
python3 tests/run_tests.py
