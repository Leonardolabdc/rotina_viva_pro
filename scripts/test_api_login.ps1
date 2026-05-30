# Teste de login Supabase na API local (Fase 1)
# Uso: .\scripts\test_api_login.ps1
# Requer API a correr: cd apps\api && python run_dev.py

$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

Write-Host "1. Health check..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 5
    Write-Host "   OK - phase: $($health.phase), supabase: $($health.supabase)" -ForegroundColor Green
} catch {
    Write-Host "   ERRO: API nao responde em $base" -ForegroundColor Red
    Write-Host "   Abra OUTRO terminal e rode:" -ForegroundColor Yellow
    Write-Host "   cd apps\api" -ForegroundColor Yellow
    Write-Host "   python run_dev.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "2. Login gestao.demo..." -ForegroundColor Cyan
$body = @{ username = "gestao.demo"; password = "demo123" } | ConvertTo-Json
try {
    $r = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Write-Host "   OK - login funcionou!" -ForegroundColor Green
    Write-Host "   role: $($r.user.role)" -ForegroundColor Green
    Write-Host "   displayName: $($r.user.displayName)" -ForegroundColor Green
    Write-Host "   token (inicio): $($r.accessToken.Substring(0, [Math]::Min(40, $r.accessToken.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ERRO no login:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "Fase 1 login: OK" -ForegroundColor Green

Write-Host "3. Listar alunos (RLS)..." -ForegroundColor Cyan
try {
    $students = Invoke-RestMethod -Uri "$base/students" -Headers @{ Authorization = "Bearer $($r.accessToken)" } -TimeoutSec 15
    $count = @($students).Count
    Write-Host "   OK - $count aluno(s) visiveis para este perfil" -ForegroundColor Green
    @($students | Select-Object -First 3) | ForEach-Object {
        Write-Host "   - $($_.id): $($_.name) ($($_.className))" -ForegroundColor Gray
    }
    if ($count -gt 3) { Write-Host "   ... e mais $($count - 3)" -ForegroundColor Gray }
} catch {
    Write-Host "   ERRO ao listar alunos:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "Fase 1 completa: login + students OK" -ForegroundColor Green
