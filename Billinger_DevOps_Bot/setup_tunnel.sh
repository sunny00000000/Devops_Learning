#!/usr/bin/env bash
# ==============================================================================
# GLOBAL REMOTE ACCESS VIA CLOUDFLARE TUNNEL (100% FREE • NO PORT FORWARDING)
# Allows accessing Billinger from phone, tablet, work laptop from anywhere.
# ==============================================================================
set -euo pipefail

PORT="${BILLINGER_PORT:-8080}"

echo "================================================================"
echo "  BILLINGER DEVOPS BOT — INSTANT GLOBAL TUNNEL SETUP"
echo "================================================================"
echo "This tool creates a secure HTTPS tunnel to access your bot"
echo "from ANY phone, tablet, or PC worldwide without port forwarding!"
echo ""

if ! command -v cloudflared >/dev/null 2>&1; then
    echo "[*] Downloading official cloudflared binary..."
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" ;;
        aarch64|arm64) URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64" ;;
        armv7l)  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm" ;;
        *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    curl -sL "$URL" -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    CLOUDFLARED="/tmp/cloudflared"
else
    CLOUDFLARED="cloudflared"
fi

echo "[*] Launching Quick HTTPS Tunnel on port ${PORT}..."
echo "----------------------------------------------------------------"
echo "Your global HTTPS URL will appear below in 3 seconds."
echo "You can open this URL on your phone or any device anywhere!"
echo "----------------------------------------------------------------"
exec "$CLOUDFLARED" tunnel --url "http://127.0.0.1:${PORT}"
