@echo off
setlocal enabledelayedexpansion

title PRAGATI AI - Industrial Energy Platform Launcher
echo ==============================================================================
echo                 PRAGATI AI: Industrial Energy & Carbon Platform
echo ==============================================================================
echo.

cd /d "%~dp0"

:: Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Copy .env if not present
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example template...
        copy .env.example .env >nul
    )
)

echo [1/3] Verifying Python runtime environment...
python --version

echo [2/3] Checking core backend dependencies...
python -c "import fastapi, uvicorn, pandas, numpy, sklearn" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required dependencies from backend/requirements.txt...
    python -m pip install -r backend/requirements.txt
)

echo [3/3] Starting PRAGATI AI FastAPI Server on http://127.0.0.1:8000 ...
echo       - Health check: http://127.0.0.1:8000/health
echo       - API Documentation: http://127.0.0.1:8000/docs
echo       - Web Dashboard: http://127.0.0.1:8000/
echo.
echo Press Ctrl+C or run stop_pragati.bat to shut down.
echo ==============================================================================
echo.

python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
