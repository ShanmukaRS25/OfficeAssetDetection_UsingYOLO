@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: start_backend.bat  –  Activate venv and launch FastAPI backend
:: ─────────────────────────────────────────────────────────────────────────────
SETLOCAL
SET SCRIPT_DIR=%~dp0
SET VENV=%SCRIPT_DIR%yolovenv

echo [1/3] Activating virtual environment...
CALL "%VENV%\Scripts\activate.bat"

echo [2/3] Checking dependencies...
pip install -q -r "%SCRIPT_DIR%requirements.txt"

echo [3/3] Starting FastAPI backend on http://localhost:8000 ...
:: IMPORTANT: must run from project root so "backend" package is importable
cd /d "%SCRIPT_DIR%"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info

ENDLOCAL
