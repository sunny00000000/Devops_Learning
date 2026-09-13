#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — PRODUCTION LINUX SETUP & SYSTEMD PROVISIONER
# Supports: Oracle Linux, Ubuntu, Debian, RHEL, CentOS, Rocky, Alma, Fedora, Arch
# Optimized for 1 CPU / 1 GB RAM lightweight execution
# ==============================================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${BILLINGER_PORT:-8080}"
HOST="${BILLINGER_HOST:-0.0.0.0}"
USER_NAME="$(whoami)"

echo "================================================================"
echo "  BILLINGER DEVOPS BOT — LINUX PRODUCTION SETUP"
echo "================================================================"
echo "Target:  Oracle Cloud Linux / Lightweight VPS (1 CPU, 1 GB RAM)"
echo "App Dir: ${APP_DIR}"
echo "User:    ${USER_NAME}"
echo "Port:    ${PORT}"
echo ""

# 1. Verify Python 3.10+
echo "[Step 1/5] Checking Python 3 Runtime..."
PYTHON_SYS=""
for cand in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY_MAJOR=$("$cand" -c "import sys; print(sys.version_info.major)")
        PY_MINOR=$("$cand" -c "import sys; print(sys.version_info.minor)")
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_SYS="$cand"
            echo "  Found: $cand (Python $PY_MAJOR.$PY_MINOR)"
            break
        fi
    fi
done

if [ -z "$PYTHON_SYS" ]; then
    echo "[ERROR] Python 3.10+ is required but not installed." >&2
    echo "Please install Python 3.10+:" >&2
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip" >&2
    echo "  Oracle/RHEL:   sudo dnf install -y python3" >&2
    exit 1
fi

# 2. Virtual Environment Setup
echo "[Step 2/5] Initializing Python Virtual Environment..."
if [ ! -d "${APP_DIR}/venv" ]; then
    echo "  Creating venv at ${APP_DIR}/venv..."
    "$PYTHON_SYS" -m venv "${APP_DIR}/venv" 2>/dev/null || {
        echo "  [Notice] venv module not found, operating with system Python."
    }
fi

if [ -f "${APP_DIR}/venv/bin/python3" ]; then
    PYTHON_EXEC="${APP_DIR}/venv/bin/python3"
else
    PYTHON_EXEC="$(command -v "$PYTHON_SYS")"
fi
echo "  Using interpreter: ${PYTHON_EXEC}"

# 3. Create Storage Directories
echo "[Step 3/5] Setting up Local Directory Structure..."
mkdir -p "${APP_DIR}/data/secure_tokens" \
         "${APP_DIR}/backups" \
         "${APP_DIR}/labs/student_1" \
         "${APP_DIR}/career_data" \
         "${APP_DIR}/certificates"

chmod +x "${APP_DIR}"/*.sh 2>/dev/null || true
echo "  Directories initialized and scripts set executable."

# 4. Configure Systemd Service
echo "[Step 4/5] Configuring Systemd (Auto-Reboot & Self-Healing)..."
SERVICE_FILE="/etc/systemd/system/billinger.service"

if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    sudo bash -c "cat << 'SVCEOF' > $SERVICE_FILE
[Unit]
Description=Billinger Enterprise DevOps & SRE Platform
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
Environment=BILLINGER_HOST=$HOST
Environment=BILLINGER_PORT=$PORT
Environment=BILLINGER_NO_BROWSER=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_EXEC app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
SVCEOF"
    sudo systemctl daemon-reload
    sudo systemctl enable billinger.service
    sudo systemctl restart billinger.service
    echo "  [OK] Systemd service enabled and started: billinger.service"
else
    # User-level systemd fallback
    mkdir -p "$HOME/.config/systemd/user"
    cat << SVCEOF > "$HOME/.config/systemd/user/billinger.service"
[Unit]
Description=Billinger Enterprise DevOps & SRE Platform
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=BILLINGER_HOST=$HOST
Environment=BILLINGER_PORT=$PORT
Environment=BILLINGER_NO_BROWSER=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_EXEC app.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
SVCEOF
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable billinger.service 2>/dev/null || true
    systemctl --user restart billinger.service 2>/dev/null || true
    echo "  [OK] User systemd service enabled: ~/.config/systemd/user/billinger.service"
fi

# 5. Run Self-Test
echo "[Step 5/5] Running Self-Test Suite..."
"$PYTHON_EXEC" "${APP_DIR}/tests/run_tests.py"

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

echo ""
echo "================================================================"
echo "  BILLINGER LINUX DEPLOYMENT COMPLETE"
echo "================================================================"
echo "  Local Web Access:    http://localhost:${PORT} or http://127.0.0.1:${PORT}"
if [ -n "$LOCAL_IP" ] && [ "$LOCAL_IP" != "127.0.0.1" ]; then
    echo "  LAN/Wi-Fi Access:    http://${LOCAL_IP}:${PORT}"
fi
echo ""
echo "Management Commands:"
echo "  ./status_billinger.sh   -> Check service status, RAM, and CPU"
echo "  ./stop_billinger.sh     -> Stop the background service"
echo "  ./start_billinger.sh    -> Start the service"
echo "  ./restart_billinger.sh  -> Restart the service"
echo "  ./backup_billinger.sh   -> Create an integrity-verified backup"
echo "  ./restore_billinger.sh  -> Restore database safely"
echo "  ./setup_tunnel.sh       -> Enable Free Global Cloudflare HTTPS Access"
echo "================================================================"
