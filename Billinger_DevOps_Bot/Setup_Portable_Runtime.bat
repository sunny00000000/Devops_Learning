@echo off
setlocal
cd /d "%~dp0"
echo [*] Setting up portable runtime...
python -c "import sqlite3, json, urllib.request; print('[OK] Standard library runtime ready.')"
python -m pip install -q reportlab fastapi uvicorn 2>nul
echo [*] Setup complete.
pause
