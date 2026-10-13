#!/usr/bin/env bash
# ==============================================================================
# PRAGATI AI - Industrial Energy Platform Launcher (Linux/macOS)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================================================="
echo "                PRAGATI AI: Industrial Energy & Carbon Platform"
echo "=============================================================================="

# Check Python command
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 was not found in PATH."
    exit 1
fi

# Ensure .env exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[INFO] Creating .env from .env.example template..."
    cp .env.example .env
fi

echo "[1/3] Verifying Python runtime environment: $($PY_CMD --version)"

echo "[2/3] Checking core backend dependencies..."
$PY_CMD -c "import fastapi, uvicorn, pandas, numpy, sklearn" 2>/dev/null || {
    echo "[INFO] Installing backend dependencies..."
    $PY_CMD -m pip install -r backend/requirements.txt
}

echo "[3/3] Starting PRAGATI AI FastAPI Server on http://0.0.0.0:8000 ..."
echo "      - Health Check: http://127.0.0.1:8000/health"
echo "      - API Docs:     http://127.0.0.1:8000/docs"
echo "      - Dashboard:    http://127.0.0.1:8000/"
echo "=============================================================================="

exec $PY_CMD -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
