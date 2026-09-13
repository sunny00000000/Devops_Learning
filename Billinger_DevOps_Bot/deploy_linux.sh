#!/usr/bin/env bash
# ==============================================================================
# BILLINGER DEVOPS BOT — 1-CLICK LINUX PRODUCTION DEPLOYMENT ENGINE
# Supports: Ubuntu, Debian, RHEL, CentOS, Rocky, Alma, Fedora, Arch, Oracle Linux
# ==============================================================================
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${BILLINGER_PORT:-8080}"
USER_NAME="$(whoami)"

echo -e "${CYAN}================================================================"
echo -e "   BILLINGER DEVOPS BOT — 1-CLICK LINUX DEPLOYMENT ENGINE v3.0.0"
echo -e "================================================================${NC}"
echo -e "Deploying from: ${GREEN}${APP_DIR}${NC}"
echo -e "Executing user: ${GREEN}${USER_NAME}${NC}"
echo ""

# 1. Verify Python 3.10+
echo -e "${CYAN}[Step 1/5] Checking Python Runtime...${NC}"
PYTHON_BIN=""
for cand in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY_VER=$("$cand" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PY_MAJOR=$("$cand" -c "import sys; print(sys.version_info.major)")
        PY_MINOR=$("$cand" -c "import sys; print(sys.version_info.minor)")
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_BIN="$cand"
            echo -e "  Found suitable runtime: ${GREEN}$cand (v$PY_VER)${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}[ERROR] Python 3.10+ is required but not installed.${NC}"
    echo "Please install Python 3.10+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    echo "  RHEL/CentOS:   sudo dnf install -y python3"
    exit 1
fi

# 2. Create runtime directories and set permissions
echo -e "${CYAN}[Step 2/5] Initializing Directory Hierarchy & State...${NC}"
mkdir -p "$APP_DIR/data/secure_tokens" "$APP_DIR/backups" "$APP_DIR/labs/student_1" "$APP_DIR/career_data" "$APP_DIR/certificates"
chmod +x "$APP_DIR"/*.sh 2>/dev/null || true
echo -e "  Runtime state initialized: ${GREEN}[OK]${NC}"

# 3. Firewall Guidance / Configuration
echo -e "${CYAN}[Step 3/5] Configuring Local Firewall (Port ${PORT})...${NC}"
if command -v ufw >/dev/null 2>&1; then
    if sudo -n true 2>/dev/null; then
        sudo ufw allow "$PORT/tcp" comment "Billinger DevOps Bot" || true
        echo -e "  UFW port ${PORT} opened: ${GREEN}[OK]${NC}"
    else
        echo -e "  ${YELLOW}Notice: Run 'sudo ufw allow $PORT/tcp' if UFW firewall is active.${NC}"
    fi
elif command -v firewall-cmd >/dev/null 2>&1; then
    if sudo -n true 2>/dev/null; then
        sudo firewall-cmd --permanent --add-port="$PORT/tcp" 2>/dev/null || true
        sudo firewall-cmd --reload 2>/dev/null || true
        echo -e "  Firewalld port ${PORT} opened: ${GREEN}[OK]${NC}"
    fi
fi

# 4. Generate Systemd Service
echo -e "${CYAN}[Step 4/5] Configuring Systemd 24/7 Background Service...${NC}"
SERVICE_FILE="/etc/systemd/system/billinger.service"

if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    sudo bash -c "cat << 'SVCEOF' > $SERVICE_FILE
[Unit]
Description=Billinger DevOps Bot Production Platform
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
Environment=BILLINGER_HOST=0.0.0.0
Environment=BILLINGER_PORT=$PORT
Environment=BILLINGER_NO_BROWSER=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$(command -v "$PYTHON_BIN") app.py
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
    echo -e "  Systemd service created & started: ${GREEN}billinger.service${NC}"
else
    # Non-root fallback: generate local user service or run in background
    mkdir -p "$HOME/.config/systemd/user"
    cat << SVCEOF > "$HOME/.config/systemd/user/billinger.service"
[Unit]
Description=Billinger DevOps Bot Production Platform
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=BILLINGER_HOST=0.0.0.0
Environment=BILLINGER_PORT=$PORT
Environment=BILLINGER_NO_BROWSER=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$(command -v "$PYTHON_BIN") app.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
SVCEOF
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable billinger.service 2>/dev/null || true
    systemctl --user restart billinger.service 2>/dev/null || true
    echo -e "  User systemd service created: ${GREEN}~/.config/systemd/user/billinger.service${NC}"
fi

# 5. Detect and Display Access IP Addresses
echo ""
echo -e "${CYAN}[Step 5/5] Deployment Successful! Access URLs:${NC}"
echo -e "----------------------------------------------------------------"

# Localhost
echo -e "  Local Browser:     ${GREEN}http://localhost:${PORT}${NC} or ${GREEN}http://127.0.0.1:${PORT}${NC}"

# Local Network IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
echo -e "  Same Wi-Fi/LAN:    ${GREEN}http://${LOCAL_IP}:${PORT}${NC}"

# Public Cloud IP if available
PUBLIC_IP=$(curl -s -m 3 ifconfig.me 2>/dev/null || curl -s -m 3 icanhazip.com 2>/dev/null || echo "")
if [ -n "$PUBLIC_IP" ]; then
    echo -e "  Global Internet:   ${GREEN}http://${PUBLIC_IP}:${PORT}${NC} (ensure cloud firewall allows port ${PORT})"
fi

echo -e "----------------------------------------------------------------"
echo -e "${YELLOW}Want 100% Free Global Access from Mobile/Anywhere with NO Port Forwarding?${NC}"
echo -e "Run: ${CYAN}./setup_tunnel.sh${NC} (Uses free Cloudflare Tunnel)"
echo -e "================================================================"
