@echo off
echo ==========================================================
echo   GenStockMarket: Indian Stock Market Paper Trading + AI
echo ==========================================================
echo.
echo Starting FastAPI Backend in a new window...
start "GenStockMarket Backend (FastAPI)" cmd /k "python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000"

echo Starting React Vite Frontend...
npm --prefix frontend run dev
