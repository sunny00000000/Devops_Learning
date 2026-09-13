@echo off
setlocal
cd /d "%~dp0"
echo [*] Running Billinger Automated Verification Suite...
python tests/run_tests.py
pause
