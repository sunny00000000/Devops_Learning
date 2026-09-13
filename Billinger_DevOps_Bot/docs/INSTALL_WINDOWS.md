# BILLINGER INSTALLATION GUIDE — WINDOWS 10 & 11

## System Requirements
- **Operating System:** Windows 10 (64-bit) or Windows 11.
- **Python:** Python 3.10, 3.11, or 3.12 installed and added to your system `PATH`.
- **Memory:** Minimum 2 GB RAM (4 GB recommended).
- **Disk Space:** 500 MB free space.

## Installation Steps
1. **Extract Archive:** Extract `Billinger_Windows_FINAL.zip` to your preferred drive (e.g. `C:\Billinger`, `D:\Billinger`, or external USB drive). Paths with spaces are supported.
2. **Setup Runtime:**
   - Double-click `Setup_Portable_Runtime.bat` (or execute `Setup_Portable_Runtime.ps1` in PowerShell).
   - This checks your Python environment and installs lightweight optional packages (`reportlab`, `fastapi`, `uvicorn`).
3. **Run Self-Test:**
   - Double-click `Run_Self_Test.bat` to run the 31-point automated verification suite. Ensure all tests pass with `OK`.
4. **Launch Application:**
   - Double-click `Start_Billinger_Bot.bat`.
   - Your browser will open automatically to `http://127.0.0.1:8080`.
