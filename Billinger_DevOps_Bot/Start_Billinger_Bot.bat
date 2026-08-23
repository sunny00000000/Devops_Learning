@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Billinger DevOps Learning Bot v2.6.2
color 0B

echo ============================================================
echo   BILLINGER DEVOPS BOT v2.6.2 - ADAPTIVE AI MENTOR EDITION
echo   Local, private, portable Windows learning environment
echo ============================================================
echo.

if exist "%~dp0runtime\python.exe" (
    "%~dp0runtime\python.exe" "%~dp0app.py"
    goto :end
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0app.py"
    goto :end
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0app.py"
    goto :end
)

echo No Python runtime was detected.
echo Billinger will perform a one-time portable runtime setup.
echo Internet is required only for this one-time setup.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup_Portable_Runtime.ps1"
if errorlevel 1 goto :runtime_error

"%~dp0runtime\python.exe" "%~dp0app.py"
goto :end

:runtime_error
echo.
echo Automatic runtime setup failed.
echo Run Setup_Portable_Runtime.bat when internet is available,
echo or install Python 3 and then start this file again.
pause
:end
endlocal
