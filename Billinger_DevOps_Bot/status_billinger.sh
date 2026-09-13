#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — STATUS SCRIPT
# Checks service status, process PID, RAM, CPU, DB, and /api/health
# ==============================================================================
set -e
cd "$(dirname "$0")"

APP_DIR="$(pwd)"
PORT="${BILLINGER_PORT:-8080}"
HOST="${BILLINGER_HOST:-127.0.0.1}"
PID_FILE="${APP_DIR}/data/billinger.pid"
DB_PATH="${BILLINGER_DB_PATH:-${APP_DIR}/data/billinger.db}"

echo "========================================================"
echo "  BILLINGER DEVOPS BOT - STATUS CHECK"
echo "========================================================"

RUNNING=0
ACTIVE_PID=""

# Check systemd status
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet billinger.service 2>/dev/null; then
    echo "[Systemd Status]: ACTIVE (Running as system-level service)"
    RUNNING=1
elif command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet billinger.service 2>/dev/null; then
    echo "[Systemd Status]: ACTIVE (Running as user-level service)"
    RUNNING=1
fi

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        RUNNING=1
        ACTIVE_PID="$PID"
    fi
fi

# Check process table if PID not in file
if [ -z "$ACTIVE_PID" ]; then
    PIDS=$(pgrep -f "python.*app\.py" || true)
    for p in $PIDS; do
        CWD=$(readlink -f /proc/$p/cwd 2>/dev/null || true)
        if [ "$CWD" = "$APP_DIR" ]; then
            ACTIVE_PID="$p"
            RUNNING=1
            break
        fi
    done
fi

if [ "$RUNNING" -eq 1 ] && [ -n "$ACTIVE_PID" ]; then
    echo "[Process]:        RUNNING (PID: $ACTIVE_PID)"
    if command -v ps >/dev/null 2>&1; then
        PS_INFO=$(ps -p "$ACTIVE_PID" -o %cpu,%mem,rss,etime --no-headers 2>/dev/null || true)
        if [ -n "$PS_INFO" ]; then
            CPU=$(echo "$PS_INFO" | awk '{print $1}')
            MEM_PCT=$(echo "$PS_INFO" | awk '{print $2}')
            RSS_KB=$(echo "$PS_INFO" | awk '{print $3}')
            UPTIME=$(echo "$PS_INFO" | awk '{print $4}')
            RSS_MB=$(awk "BEGIN {printf \"%.1f\", $RSS_KB/1024}")
            echo "[Resource]:       CPU: ${CPU}% | RAM: ${RSS_MB} MB (${MEM_PCT}%) | Uptime: ${UPTIME}"
        fi
    fi
elif [ "$RUNNING" -eq 1 ]; then
    echo "[Process]:        RUNNING (Managed by Systemd)"
else
    echo "[Process]:        STOPPED"
fi

# Check Database
if [ -f "$DB_PATH" ]; then
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "[Database]:       SQLite OK (${DB_SIZE} at ${DB_PATH})"
else
    echo "[Database]:       Not initialized yet (${DB_PATH})"
fi

# Query Health Endpoint
HEALTH_URL="http://127.0.0.1:${PORT}/api/health"
echo "[Health Probe]:   Checking ${HEALTH_URL}..."
HEALTH_RESP=""
if command -v curl >/dev/null 2>&1; then
    HEALTH_RESP=$(curl -s -m 4 "$HEALTH_URL" 2>/dev/null || curl -s -m 4 "http://localhost:${PORT}/api/health" 2>/dev/null || true)
elif command -v wget >/dev/null 2>&1; then
    HEALTH_RESP=$(wget -qO- --timeout=4 "$HEALTH_URL" 2>/dev/null || true)
fi

if [ -n "$HEALTH_RESP" ]; then
    echo "                  Response: ${HEALTH_RESP:0:150}..."
    echo "[Health Status]:  HEALTHY (HTTP 200 OK)"
else
    if [ "$RUNNING" -eq 1 ]; then
        echo "[Health Status]:  STARTING_UP (Process is initializing, retry in a moment)"
    else
        echo "[Health Status]:  STOPPED (Service not running)"
    fi
fi
echo "========================================================"
