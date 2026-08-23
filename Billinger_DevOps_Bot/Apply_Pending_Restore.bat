@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Billinger Backup Restore Manager
color 0E
echo ============================================================
echo   BILLINGER BOT - APPLY STAGED RESTORE
echo ============================================================
echo Close the main Billinger Bot window before continuing.
echo.
if exist "runtime\python.exe" (
  "runtime\python.exe" "offline_maintenance.py" restore
) else (
  where py >nul 2>nul && (py -3 "offline_maintenance.py" restore) || (python "offline_maintenance.py" restore)
)
if errorlevel 1 (echo.&echo Restore was not applied.) else (echo.&echo Restore completed. Start Billinger Bot normally.)
pause
endlocal
