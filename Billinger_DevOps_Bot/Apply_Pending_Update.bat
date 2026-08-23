@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Billinger Offline Update Manager
color 0B
echo ============================================================
echo   BILLINGER BOT - APPLY STAGED UPDATE
echo ============================================================
echo Close the main Billinger Bot window before continuing.
echo.
if exist "runtime\python.exe" (
  "runtime\python.exe" "offline_maintenance.py" update
) else (
  where py >nul 2>nul && (py -3 "offline_maintenance.py" update) || (python "offline_maintenance.py" update)
)
if errorlevel 1 (echo.&echo Update was not applied.) else (echo.&echo Update completed. Start Billinger Bot normally.)
pause
endlocal
