@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHON_CMD="
if exist "runtime\python.exe" set "PYTHON_CMD=runtime\python.exe"
if not defined PYTHON_CMD where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  echo Python runtime not found. Run Start_Billinger_Bot.bat first.
  pause
  exit /b 1
)

echo Running Billinger v2.7 unit, regression, readiness, AI, security, and HTTP tests...
%PYTHON_CMD% -m unittest discover -s tests -v
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test_v2.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test_v3.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test_v4.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test_v6.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\smoke_test_v7.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\security_http_test.py
if errorlevel 1 goto :failed

echo.
echo ALL BILLINGER v2.7 CORE, READINESS, AI, CAREER, PORTFOLIO, AND SECURITY TESTS PASSED
pause
exit /b 0

:failed
echo.
echo SELF TEST FAILED. Review the error above and do not apply external updates until corrected.
pause
exit /b 1
