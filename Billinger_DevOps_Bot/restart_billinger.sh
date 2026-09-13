#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — RESTART SCRIPT
# Restarts Billinger service gracefully and validates health
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "========================================================"
echo "  BILLINGER DEVOPS BOT - RESTARTING SERVICE"
echo "========================================================"

if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet billinger.service 2>/dev/null; then
    echo "[*] Restarting systemd billinger.service..."
    if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
        sudo systemctl restart billinger.service
    else
        echo "[!] Using sudo to restart system service..."
        sudo systemctl restart billinger.service
    fi
elif command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet billinger.service 2>/dev/null; then
    echo "[*] Restarting user systemd billinger.service..."
    systemctl --user restart billinger.service
else
    ./stop_billinger.sh
    sleep 1
    ./start_billinger.sh --daemon
fi

sleep 1
./status_billinger.sh
