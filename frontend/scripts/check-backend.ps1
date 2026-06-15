$ErrorActionPreference = "Stop"
try {
    Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2 | Out-Null
    Write-Host "[WildTrail] Backend OK (http://127.0.0.1:8000)"
    exit 0
} catch {
    Write-Host ""
    Write-Host "[WildTrail] Backend is not running on port 8000." -ForegroundColor Yellow
    Write-Host "Start it in another terminal:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\activate" -ForegroundColor Cyan
    Write-Host "  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
