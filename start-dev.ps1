# GenStockMarket One-Click Local Launcher
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  GenStockMarket: Indian Stock Market Paper Trading + AI  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check Python and Uvicorn
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'FastAPI Backend running at http://localhost:8000 (Docs: http://localhost:8000/docs)' -ForegroundColor Green; python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000"

# Start Frontend in current shell
Write-Host "[2/2] Starting React Vite Frontend on http://localhost:5173...`n" -ForegroundColor Green
npm --prefix frontend run dev
