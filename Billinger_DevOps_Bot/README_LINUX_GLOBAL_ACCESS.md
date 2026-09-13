# BILLINGER DEVOPS BOT — LINUX CLOUD & GLOBAL ACCESS GUIDE
**Target Environment:** Oracle Cloud Linux VM / Lightweight Cloud VPS (1 CPU, 1 GB RAM)  
**Release:** Production v3.0.0 (Zero Heavyweight Dependencies • No Docker/K8s Required)

---

## 1. Overview & Architecture

Billinger is optimized for lightweight Linux cloud deployment. It runs directly inside a standard Python 3.10+ virtual environment (`venv`) backed by SQLite and local storage, consuming only **~30 MB of RAM** at idle.

### Global Zero-Trust Architecture
```text
[Global User: Phone / Laptop / Tablet]
                 │ (Any network, Wi-Fi, 4G/5G, or Country)
                 ▼
     [Cloudflare Edge Network] (Free SSL/TLS & DDoS Protection)
                 │
                 ▼
     [Cloudflare Access] (Zero-Trust Email OTP / OAuth Authentication)
                 │
                 ▼
     [Cloudflare Tunnel (cloudflared)]
                 │
                 ▼ (Secure outbound-only localhost loopback)
       127.0.0.1:8080 ───► [Billinger Application Server]
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                  [SQLite Database]     [Local Vault Storage]
```
* **Zero Public Port Exposure:** Application port 8080 does not need to be opened to the public Internet.
* **Administrative Access:** SSH is secured via **Tailscale SSH**, keeping port 22 closed to the public Internet.

---

## 2. Complete List of Linux Management Scripts

| Script | Function |
| :--- | :--- |
| `./setup_linux.sh` | 1-click installer: initializes `venv`, storage directories, and configures systemd 24/7 service. |
| `./setup_portable_runtime.sh` | Initializes directory structure and local virtual environment without requiring root/sudo privileges. |
| `./start_billinger.sh` | Starts the server (foreground or `--daemon` background mode). |
| `./stop_billinger.sh` | Gracefully stops the service (systemd or PID). |
| `./restart_billinger.sh` | Restarts the server and performs an immediate health check. |
| `./status_billinger.sh` | Probes service state, active PID, live CPU%, RAM (MB), database size, and `/api/health`. |
| `./run_self_test.sh` | Executes full 31-test cross-platform verification suite (100% pass). |
| `./backup_billinger.sh` | Generates a timestamped, SHA-256 verified ZIP backup of SQLite state and user data. |
| `./restore_billinger.sh` | Restores database state with SHA-256 integrity validation and automatic pre-restore rollback protection. |
| `./setup_tunnel.sh` | Launches an instant, zero-configuration Cloudflare Tunnel for secure global HTTPS access. |

---

## 3. Step-by-Step: Uploading to Linux VM & Starting

### Step 1: Upload the Linux Package
From your local machine (Windows PowerShell, macOS, or Linux Terminal), upload `Billinger_Linux_FINAL.zip` to your Oracle Cloud VM:

```bash
# Using SCP (replace with your server IP and private key)
scp -i ~/.ssh/oracle_key.key Billinger_Linux_FINAL.zip opc@<YOUR_VM_IP>:~/
```
*(Or use SFTP / FileZilla / WinSCP if you prefer a graphical interface).*

### Step 2: Connect via SSH & Unzip
```bash
ssh -i ~/.ssh/oracle_key.key opc@<YOUR_VM_IP>

# Install unzip if not already present
# Oracle Linux / RHEL:
sudo dnf install -y unzip
# Ubuntu / Debian:
# sudo apt update && sudo apt install -y unzip

# Extract the package
unzip Billinger_Linux_FINAL.zip
cd Billinger_DevOps_Bot
```

### Step 3: Run 1-Click Automated Setup
```bash
chmod +x *.sh
./setup_linux.sh
```
`setup_linux.sh` automatically:
1. Detects Python 3.10+ (and sets up `venv/`).
2. Creates storage directories (`data/secure_tokens`, `backups`, `labs/student_1`, etc.).
3. Generates `/etc/systemd/system/billinger.service` with:
   - `Restart=always` and `RestartSec=5` for automatic recovery from unexpected crashes.
   - Auto-start on system reboot (`WantedBy=multi-user.target`).
4. Reloads systemd daemon and starts the service.
5. Runs the automated self-test suite.

---

## 4. Configuring Free Global Access via Cloudflare Tunnel

Access Billinger securely from any smartphone, tablet, or PC worldwide without opening firewall ports.

### Quick Ephemeral Tunnel (Testing)
Inside the `Billinger_DevOps_Bot` directory:
```bash
./setup_tunnel.sh
```
`cloudflared` outputs a public URL (e.g., `https://random-subdomain.trycloudflare.com`). You can open this URL immediately on any device in the world.

### Permanent Production Tunnel (Zero Trust Domain)
1. Sign up for a free Cloudflare account at [cloudflare.com](https://cloudflare.com).
2. Go to **Zero Trust Dashboard** > **Networks** > **Tunnels** > **Create a Tunnel**.
3. Choose **Cloudflared**, name it `billinger-tunnel`, and select your operating system (Linux x86_64 / arm64).
4. Run the provided installation command on your VM:
   ```bash
   sudo cloudflared service install <YOUR_TUNNEL_TOKEN>
   ```
5. In the Cloudflare dashboard, add a **Public Hostname**:
   - Subdomain: `billinger.yourdomain.com`
   - Service Type: `HTTP`
   - URL: `127.0.0.1:8080`
6. Add **Cloudflare Access (Zero Trust Authentication)**:
   - Enable an Access Application on `billinger.yourdomain.com`.
   - Set policy to require a **One-Time PIN (OTP)** sent to your personal email address.
   - Only you can authenticate, while your app stays completely shielded behind Cloudflare.

---

## 5. Administrative SSH via Tailscale (No Exposed Port 22)

To manage your server securely without exposing port 22 to public brute-force attacks:

### Step 1: Install Tailscale on the Linux VM
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### Step 2: Authenticate with Tailscale SSH Enabled
```bash
sudo tailscale up --ssh
```
Visit the login link printed in the terminal to authorize the machine to your Tailscale network.

### Step 3: Connect Securely
Install the Tailscale client on your laptop or phone. You can now SSH directly using the private Tailscale IP or machine name:
```bash
ssh opc@billinger-vm
```

### Step 4: Access Control & Device Revocation
- **Access Control:** Manage access rules directly in the [Tailscale Admin Console](https://login.tailscale.com/admin).
- **Key Expiry & Disconnect:** Force key re-authentication or disconnect immediately via `sudo tailscale down`.
- **Device Removal:** Click **Remove Device** from the Tailscale Admin Console to permanently revoke server access.

---

## 6. Cloud Failure Handling & Self-Healing Matrix

Billinger includes built-in resilience mechanisms tested against common cloud failure conditions:

| Failure Scenario | Built-in Protection & Recovery Mechanism |
| :--- | :--- |
| **Server Reboot** | Systemd unit (`billinger.service`) is enabled to start automatically on boot. |
| **App Crash / OOM** | Systemd automatically restarts the process within 5 seconds (`Restart=always`, `RestartSec=5`). |
| **Internet / DNS Outage** | Billinger runs 100% offline-ready: local SQLite database, embedded curriculum catalog, and local sandbox remain functional. |
| **Cloudflare Tunnel Drop** | Localhost binding (`127.0.0.1:8080`) and LAN IP remain active; administrative access through Tailscale continues uninterrupted. |
| **AI Provider Failure / 429** | Multi-provider AI router automatically falls back across Gemini ➔ Groq ➔ OpenAI ➔ OpenRouter ➔ Offline local cache. |
| **AI API Timeout** | Timeouts are trapped cleanly within 15 seconds, returning actionable guidance without hanging the server thread. |
| **Corrupted Backup Restore** | `restore_billinger.sh` verifies SHA-256 checksums before applying any backup. If a mismatch is detected, restoration is rejected and the existing database is preserved. |
| **Database Failure** | A pre-restore rollback snapshot (`pre_restore_snapshot_*.db`) is created automatically before any schema or data modifications. |
| **Low Disk Pressure** | Lightweight storage engine: zero bulky dependencies, automatic log sanitization, and manual/automated backup rotation. |

---

## 7. Performance & Resource Benchmarks (1 CPU, 1 GB RAM)

Verified on Oracle Cloud Linux / Debian Linux x86_64:

- **Idle Memory Footprint:** `~30.8 MB` (~3% of 1 GB RAM total)
- **Idle CPU Utilization:** `< 0.2%`
- **Application Startup Time:** `1.15 seconds`
- **Total Distribution Size:** `< 20 MB` (complete platform including all 12 modules and docs)
- **Health Check Response Time:** `< 4 ms` (`GET /api/health` ➔ 200 OK)
- **Self-Test Suite Runtime:** `< 2.2 seconds` (31/31 tests passing)

---

## 8. Security & Secret Protection

- **No Secrets in Logs:** Structured logging uses regex pattern masking to redact API keys, session tokens, passwords, and Authorization headers.
- **Port Isolation:** Binds to `127.0.0.1` by default when routed through Cloudflare Tunnel.
- **HTTP Security Headers:** Every HTTP response includes `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
- **Command Sandbox Security:** Multi-tier execution sandbox classifies commands into SAFE, CAUTION, and DESTRUCTIVE, blocking dangerous system modifications.
