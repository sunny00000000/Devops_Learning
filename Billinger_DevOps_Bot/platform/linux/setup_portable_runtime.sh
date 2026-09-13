#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "[*] Setting up Billinger Linux Runtime Environment..."
python3 -c "import sqlite3, json, urllib.request; print('[OK] Standard library runtime ready.')"
python3 -m pip install -q reportlab fastapi uvicorn 2>/dev/null || true
echo "[*] Setup complete."
