# BILLINGER DEVOPS BOT — LINUX DEPLOYMENT & GLOBAL ACCESS GUIDE

This guide provides complete instructions for deploying Billinger on any Linux machine (Cloud VPS, Raspberry Pi, home server, or local PC) and accessing it from any device (phone, tablet, laptop) anywhere in the world.

---

## 1. Fast 1-Command Linux Deployment

On your Linux machine (Ubuntu, Debian, RHEL, Oracle Cloud, AWS EC2):
```bash
# 1. Extract the package
unzip Billinger_DevOps_Bot_Linux_v3.0.0_Complete.zip
cd Billinger_DevOps_Bot

# 2. Run the automated deployment script
chmod +x deploy_linux.sh
./deploy_linux.sh
```

`deploy_linux.sh` automatically:
1. Validates Python 3.10+ runtime.
2. Initializes runtime directories (`data/`, `labs/`, `backups/`).
3. Opens firewall port `8080` (UFW / firewalld).
4. Creates, enables, and starts a systemd service (`billinger.service`) to keep the bot running 24/7 and auto-restart on system reboot.
5. Displays your exact LAN and Public IP access URLs.

---

## 2. Accessing from Any Device Anywhere in the World

Choose the method that fits your setup:

### Method A: Free Cloudflare Tunnel (Recommended — No Port Forwarding, No Public IP Needed)
Works even on home PCs, behind college/office firewalls, and mobile hot-spots (CGNAT):
1. Inside `Billinger_DevOps_Bot`, run:
   ```bash
   ./setup_tunnel.sh
   ```
2. Cloudflare will generate a secure global HTTPS URL:
   ```
   https://random-words-subdomain.trycloudflare.com
   ```
3. Open this HTTPS URL on your **smartphone (iOS/Android)**, **tablet**, or **work laptop** from anywhere in the world.

---

### Method B: Cloud VPS (Oracle Cloud Free Tier / AWS EC2 / DigitalOcean)
If you deploy on a cloud server with a Public IP:
1. In your Cloud Console (e.g. Oracle Cloud Virtual Cloud Network Security List, or AWS Security Group):
   - Add an **Ingress Rule**: Protocol: `TCP`, Port Range: `8080`, Source CIDR: `0.0.0.0/0`.
2. Access directly via browser:
   ```
   http://<YOUR_CLOUD_PUBLIC_IP>:8080
   ```
3. (Optional) Put Nginx and a free Let's Encrypt SSL certificate in front using `deploy/nginx/billinger.conf`:
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   sudo cp deploy/nginx/billinger.conf /etc/nginx/sites-available/billinger
   sudo ln -s /etc/nginx/sites-available/billinger /etc/nginx/sites-enabled/
   sudo certbot --nginx -d yourdomain.com
   ```

---

### Method C: Tailscale Private Mesh VPN (100% Private & Secure)
1. Install Tailscale on your Linux host: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
2. Install the Tailscale app on your phone / laptop and sign in with the same account.
3. Access Billinger using the host's 100.x.y.z Tailscale IP:
   ```
   http://100.x.y.z:8080
   ```

---

### Method D: Docker Container Deployment
If you prefer running in Docker:
```bash
# Start containerized stack in background
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down
```

---

## 3. Useful Service Commands (Systemd)

- Check service status: `systemctl status billinger`
- View live application logs: `journalctl -u billinger -f`
- Restart service: `sudo systemctl restart billinger`
- Stop service: `sudo systemctl stop billinger`
