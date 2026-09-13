#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================================"
echo "  BILLINGER DEVOPS BOT - LINUX RUNNER v3.0.0"
echo "========================================================"

PYTHON_BIN=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python 3.10+ required but not found in PATH." >&2
    exit 1
fi

export BILLINGER_HOST="${BILLINGER_HOST:-0.0.0.0}"
export BILLINGER_PORT="${BILLINGER_PORT:-8080}"
export PYTHONUNBUFFERED=1

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

echo "[*] Server listening on all interfaces (0.0.0.0:${BILLINGER_PORT})"
echo "[*] Open in browser using:"
echo "    -> Local browser:  http://localhost:${BILLINGER_PORT}  or  http://127.0.0.1:${BILLINGER_PORT}"
if [ -n "$LOCAL_IP" ] && [ "$LOCAL_IP" != "127.0.0.1" ]; then
    echo "    -> Other devices:  http://${LOCAL_IP}:${BILLINGER_PORT} (same Wi-Fi / LAN)"
fi
echo ""
exec "$PYTHON_BIN" app.py "$@"
