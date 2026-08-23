@echo off
setlocal
cd /d "%~dp0"
echo This removes all student profiles, learning progress, tests, interviews,
echo company work, capstone reviews, resume records, and safe-lab files.
set /p CONFIRM=Type RESET to continue: 
if /I not "%CONFIRM%"=="RESET" goto :cancel
if exist "data\billinger.db" del /f /q "data\billinger.db"
if exist "data\billinger.db-wal" del /f /q "data\billinger.db-wal"
if exist "data\billinger.db-shm" del /f /q "data\billinger.db-shm"
for /d %%D in ("labs\student_*") do rd /s /q "%%~fD"
echo Local data reset. A clean database will be created on next launch.
pause
goto :end
:cancel
echo Reset cancelled.
pause
:end
endlocal
