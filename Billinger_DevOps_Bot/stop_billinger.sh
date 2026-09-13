#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — STOP SCRIPT
# Gracefully stops Billinger service (Systemd, PID file, or local process)
# ==============================================================================
set -e
cd "$(dirname "$0")"

APP_DIR="$(pwd)"
PID_FILE="${APP_DIR}/data/billinger.pid"

echo "========================================================"
echo "  BILLINGER DEVOPS BOT - STOPPING SERVICE"
echo "========================================================"

STOPPED=0

# 1. Check systemd service if active
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet billinger.service 2>/dev/null; then
        echo "[*] Stopping system-level billinger.service..."
        if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
            sudo systemctl stop billinger.service
            STOPPED=1
        else
            echo "[!] Sudo required to stop system service: sudo systemctl stop billinger.service"
        fi
    fi
    if systemctl --user is-active --quiet billinger.service 2>/dev/null; then
        echo "[*] Stopping user-level billinger.service..."
        systemctl --user stop billinger.service
        STOPPED=1
    fi
fi

# 2. Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[*] Terminating process PID ${PID}..."
        kill -TERM "$PID" 2>/dev/null || true
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        if kill -0 "$PID" 2>/dev/null; then
            echo "[*] Process still running. Sending SIGKILL..."
            kill -KILL "$PID" 2>/dev/null || true
        fi
        STOPPED=1
    fi
    rm -f "$PID_FILE"
fi

# 3. Check for any running python processes in APP_DIR
ROGUE_PIDS=$(pgrep -f "python.*app\.py" || true)
if [ -n "$ROGUE_PIDS" ]; then
    for rpid in $ROGUE_PIDS; do
        CWD=$(readlink -f /proc/$rpid/cwd 2>/dev/null || true)
        if [ "$CWD" = "$APP_DIR" ]; then
            echo "[*] Terminating process instance PID ${rpid}..."
            kill -TERM "$rpid" 2>/dev/null || true
            sleep 0.5
            kill -9 "$rpid" 2>/dev/null || true
            STOPPED=1
        fi
    done
fi

if [ "$STOPPED" -eq 1 ]; then
    echo "[OK] Billinger service stopped successfully."
else
    echo "[*] No active Billinger process was found."
fi
