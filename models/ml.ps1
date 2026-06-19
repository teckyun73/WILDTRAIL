# WildTrail ML scripts — always use backend venv (torch installed there).
$ErrorActionPreference = "Stop"

$VenvPython = Join-Path $PSScriptRoot "..\backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host ""
    Write-Host "[WildTrail] backend/.venv not found." -ForegroundColor Yellow
    Write-Host "Create and install dependencies:" -ForegroundColor Yellow
    Write-Host "  cd ..\backend" -ForegroundColor Cyan
    Write-Host "  python -m venv .venv" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\activate" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

if ($args.Count -eq 0) {
    Write-Host "Usage: .\ml.ps1 <script.py> [args...]" -ForegroundColor Yellow
    Write-Host "Example: .\ml.ps1 evaluate.py --output ..\reports" -ForegroundColor Cyan
    exit 1
}

$Script = $args[0]
$ScriptArgs = @()
if ($args.Count -gt 1) {
    $ScriptArgs = $args[1..($args.Count - 1)]
}

Push-Location $PSScriptRoot
try {
    & $VenvPython $Script @ScriptArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
