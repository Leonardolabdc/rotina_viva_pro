# Arranca Next.js (Fase 5) em :3000
# Uso: .\scripts\start_web_dev.ps1
# Requer: API em http://127.0.0.1:8000 (start_api_dev.ps1)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $root "apps\web"

if (-not (Test-Path (Join-Path $webDir ".env.local"))) {
    Copy-Item (Join-Path $webDir ".env.local.example") (Join-Path $webDir ".env.local")
    Write-Host "Criado apps/web/.env.local a partir do exemplo." -ForegroundColor Yellow
}

Push-Location $webDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "A instalar dependencias (npm)..." -ForegroundColor Cyan
        npm install
    }
    Write-Host "Next.js em http://localhost:3000" -ForegroundColor Green
    npm run dev
} finally {
    Pop-Location
}
