#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — BACKUP SCRIPT
# Creates a timestamped, SHA-256 verified backup archive in backups/
# ==============================================================================
set -e
cd "$(dirname "$0")"

APP_DIR="$(pwd)"

if [ -f "${APP_DIR}/venv/bin/python3" ]; then
    PYTHON_BIN="${APP_DIR}/venv/bin/python3"
elif [ -f "${APP_DIR}/venv/bin/python" ]; then
    PYTHON_BIN="${APP_DIR}/venv/bin/python"
else
    PYTHON_BIN=$(command -v python3 || command -v python || true)
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python 3.10+ required but not found in venv or PATH." >&2
    exit 1
fi

echo "========================================================"
echo "  BILLINGER DEVOPS BOT - CREATING SAFE BACKUP"
echo "========================================================"

LABEL="${1:-manual_linux}"

"$PYTHON_BIN" -c "
import sys
from pathlib import Path
sys.path.insert(0, '$APP_DIR')
from storage.backup_manager import backup_manager

res = backup_manager.create_backup(label='$LABEL')
print('[SUCCESS] Backup created successfully:')
print(f\"  Archive:  {res['filename']}\")
print(f\"  Location: {res['path']}\")
print(f\"  Size:     {res['size_bytes'] / 1024:.1f} KB\")
print(f\"  SHA256:   {res['sha256']}\")
"
