# Arranca a API FastAPI no venv (liberta porta 8000 antes)
# Uso: .\scripts\start_api_dev.ps1

$ErrorActionPreference = "Stop"
$apiDir = "d:\Dev\rotina_viva_pro\apps\api"
$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "venv nao encontrado. Rode:" -ForegroundColor Yellow
    Write-Host "  cd $apiDir" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements-worker.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "A libertar porta 8000..." -ForegroundColor Cyan
$lines = netstat -ano | Select-String ":8000\s"
$pids = @()
foreach ($line in $lines) {
    if ($line -match "\s+(\d+)\s*$") {
        $pids += [int]$Matches[1]
    }
}
$pids = $pids | Sort-Object -Unique
foreach ($procId in $pids) {
    try {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "  parou PID $procId" -ForegroundColor Gray
    } catch {}
}
Start-Sleep -Seconds 2

Write-Host "A arrancar API (venv, sem reload se LLM Guard activo)..." -ForegroundColor Cyan
Set-Location $apiDir
& $venvPython run_dev.py
