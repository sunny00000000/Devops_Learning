#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — RESTORE SCRIPT
# Restores SQLite state with SHA-256 verification and pre-restore rollback
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
echo "  BILLINGER DEVOPS BOT - RESTORING BACKUP"
echo "========================================================"

TARGET="${1:-}"

"$PYTHON_BIN" -c "
import sys
import glob
import os
from pathlib import Path
sys.path.insert(0, '$APP_DIR')
from storage.backup_manager import backup_manager
from core.configuration.config import BACKUP_DIR

target = '$TARGET'
if not target:
    backups = sorted(glob.glob(str(BACKUP_DIR / 'billinger_backup_*.zip')), key=os.path.getmtime)
    if not backups:
        print('[ERROR] No backups found in backups/ directory.')
        sys.exit(1)
    target = backups[-1]
    print(f'[*] No backup specified. Using most recent: {os.path.basename(target)}')

res = backup_manager.restore_backup(target)
print(f\"[SUCCESS] {res['status']}: Restored from {res['restored_from']}\")
"
