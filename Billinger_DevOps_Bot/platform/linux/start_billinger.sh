#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "========================================================"
echo "  BILLINGER DEVOPS BOT - LINUX RUNNER v3.0.0"
echo "========================================================"
exec python3 app.py
