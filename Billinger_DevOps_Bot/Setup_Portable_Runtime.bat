@echo off
setlocal
cd /d "%~dp0"
title Billinger Portable Runtime Setup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup_Portable_Runtime.ps1"
if errorlevel 1 (
  echo.
  echo Portable runtime setup failed. Check the internet connection or install Python 3 manually.
  pause
  exit /b 1
)
echo.
echo Runtime setup completed. You can now start Billinger Bot.
pause
endlocal
