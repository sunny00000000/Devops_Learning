@echo off
setlocal
cd /d "%~dp0"
title Billinger DevOps Bot v3.0.0
echo ========================================================
echo   BILLINGER DEVOPS BOT - PRODUCTION LAUNCHER (WINDOWS)
echo ========================================================
echo.

set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python 3.10+ not found in PATH.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py -3
    )
)

echo [*] Launching Billinger Platform on http://127.0.0.1:8080...
%PYTHON_CMD% app.py
pause
