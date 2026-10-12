@echo off
title Open Business ERP - Local Invoicing & Billing System
color 0b
echo ================================================================
echo               OPEN BUSINESS ERP BILLING SYSTEM
echo        Fast, Local & Privacy-First Business ERP & Invoicing
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python runtime...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not found. Please ensure Python 3.10+ is installed from python.org.
        pause
        exit /b
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

echo [2/3] Checking environment dependencies...
%PY_CMD% -m pip install -r requirements.txt >nul 2>&1

echo [3/3] Launching Open ERP Server...
echo.
echo Server running at: http://localhost:8000
echo Tip: Install this as a native Desktop App via Chrome/Edge address bar!
echo.

:: Launch browser after 2 seconds in background
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start Uvicorn server
%PY_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
