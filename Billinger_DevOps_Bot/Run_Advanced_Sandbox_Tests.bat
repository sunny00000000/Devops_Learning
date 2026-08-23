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
echo This suite uses only temporary local databases and mocked external services.
%PYTHON_CMD% -m unittest tests.test_security_v24 tests.test_all_scenarios_v24 tests.test_v27_features -v
if errorlevel 1 goto :failed
%PYTHON_CMD% tests\security_http_test.py
if errorlevel 1 goto :failed
echo ADVANCED SANDBOX AND ADVERSARIAL TESTS PASSED
pause
exit /b 0
:failed
echo ADVANCED SANDBOX TEST FAILED
pause
exit /b 1
