@echo off
setlocal enabledelayedexpansion

REM Change to script directory
cd /d %~dp0

REM Set PYTHONPATH
set PYTHONPATH=%cd%

REM Check for --reset flag
if "%1"=="--reset" (
    echo 🧹 Removing .venv...
    rmdir /s /q .venv
)

REM Check if virtual environment exists
if not exist .venv (
    echo 🛠️  .venv not found, creating...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo ❌ requirements.txt not found!
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Launch the server
echo 🚀 Launching server...
uvicorn backend.app.main:app ^
    --host 0.0.0.0 ^
    --port 8000 ^
    --workers 4 ^
    --log-level info ^
    --timeout-keep-alive 60
