@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: start_frontend.bat  –  Install Node deps and launch Vite dev server
:: ─────────────────────────────────────────────────────────────────────────────
SETLOCAL
SET SCRIPT_DIR=%~dp0
SET FRONTEND=%SCRIPT_DIR%frontend

echo [1/2] Installing Node dependencies...
cd /d "%FRONTEND%"
npm install

echo [2/2] Starting Vite dev server on http://localhost:5173 ...
npm run dev

ENDLOCAL
