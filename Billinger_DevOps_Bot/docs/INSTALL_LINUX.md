# BILLINGER INSTALLATION GUIDE — LINUX (DEBIAN / UBUNTU / RHEL / ARCH)

## System Requirements
- **Operating System:** Any modern Linux distribution (Ubuntu 20.04+, Debian 11+, RHEL/CentOS 8+, Fedora, Arch).
- **Python:** Python 3.10+ installed (`python3 --version`).
- **Memory:** Minimum 2 GB RAM (4 GB recommended).
- **Disk Space:** 500 MB free space.

## Installation Steps
1. **Extract Archive:**
   ```bash
   unzip Billinger_Linux_FINAL.zip -d ~/Billinger
   cd ~/Billinger
   ```
2. **Make Scripts Executable:**
   ```bash
   chmod +x *.sh platform/linux/*.sh
   ```
3. **Setup Runtime Environment:**
   ```bash
   ./setup_portable_runtime.sh
   ```
4. **Run Verification Test Suite:**
   ```bash
   ./run_self_test.sh
   ```
   Verify that all 31 unit, integration, security, and cross-platform tests pass.
5. **Start Billinger:**
   ```bash
   ./start_billinger.sh
   ```
6. Open your browser and navigate to `http://127.0.0.1:8080`.
