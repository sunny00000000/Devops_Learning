@echo off
setlocal
cd /d "%~dp0"
echo [*] Resetting Billinger Local State...
if exist "data\billinger.db" del /f /q "data\billinger.db"
echo [*] Rebuilding clean database...
python -c "from storage.db import db; db.verify_schema(); print('Database reset to clean baseline.')"
pause
