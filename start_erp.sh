#!/usr/bin/env bash
# Open Business ERP - Launcher for Linux and macOS

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "================================================================"
echo "               OPEN BUSINESS ERP BILLING SYSTEM"
echo "        Fast, Local & Privacy-First Business ERP & Invoicing"
echo "================================================================"
echo ""

# Find Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 was not found. Please install Python 3.10+."
    exit 1
fi

echo "[1/3] Checking environment dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt >/dev/null 2>&1 || true

echo "[2/3] Initializing local database..."
$PYTHON_CMD -c "from app.database import init_db; init_db()"

echo "[3/3] Launching Open ERP Server..."
echo "Server running at: http://localhost:8000"
echo ""

# Attempt to open browser in background
if command -v xdg-open &>/dev/null; then
    (sleep 2 && xdg-open "http://localhost:8000") &
elif command -v open &>/dev/null; then
    (sleep 2 && open "http://localhost:8000") &
fi

# Run Uvicorn server
$PYTHON_CMD -m uvicorn app.main:app --host 127.0.0.1 --port 8000
