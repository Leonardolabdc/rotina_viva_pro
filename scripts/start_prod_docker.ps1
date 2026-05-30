# Sobe stack de producao local (API worker Docker)
# Uso: .\scripts\start_prod_docker.ps1
# Requer: Docker Desktop + .env na raiz

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Host "Crie .env na raiz (copy .env.example .env)" -ForegroundColor Red
    exit 1
}

Push-Location $root
try {
    Write-Host "A construir e subir api-worker (docker-compose.prod.yml)..." -ForegroundColor Cyan
    docker compose -f docker-compose.prod.yml up --build -d
    Write-Host ""
    Write-Host "API: http://127.0.0.1:8000/health" -ForegroundColor Green
    Write-Host "Next.js (dev): .\scripts\start_web_dev.ps1 -> http://localhost:3000" -ForegroundColor Green
    Write-Host "Streamlit legado: docker compose -f docker-compose.legacy.yml up -d" -ForegroundColor Gray
} finally {
    Pop-Location
}
