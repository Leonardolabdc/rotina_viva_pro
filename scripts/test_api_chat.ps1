# Teste de chat na API local (Fase 3)
# Uso: .\scripts\test_api_chat.ps1
# Requer: API com requirements-worker.txt + .env com Supabase e OpenRouter

$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

Write-Host "1. Health check..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 5
    Write-Host "   OK - phase: $($health.phase), supabase: $($health.supabase)" -ForegroundColor Green
} catch {
    Write-Host "   ERRO: API nao responde em $base" -ForegroundColor Red
    Write-Host "   cd apps\api && pip install -r requirements-worker.txt && python run_dev.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "2. Login gestao.demo..." -ForegroundColor Cyan
$body = @{ username = "gestao.demo"; password = "demo123" } | ConvertTo-Json
try {
    $r = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Write-Host "   OK - role: $($r.user.role)" -ForegroundColor Green
} catch {
    Write-Host "   ERRO no login:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

$headers = @{ Authorization = "Bearer $($r.accessToken)" }

Write-Host "3. Criar sessao de chat..." -ForegroundColor Cyan
try {
    $session = Invoke-RestMethod -Uri "$base/chat/sessions" -Method POST -Headers $headers `
        -ContentType "application/json" -Body (@{ dataSourceMode = "auto" } | ConvertTo-Json) -TimeoutSec 15
    Write-Host "   OK - session id: $($session.id)" -ForegroundColor Green
} catch {
    Write-Host "   ERRO ao criar sessao:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
    exit 1
}

Write-Host "4. Enviar mensagem (sync)..." -ForegroundColor Cyan
$msgBody = @{ content = "Quantos alunos temos no cadastro? Responda em uma frase." } | ConvertTo-Json
try {
    $reply = Invoke-RestMethod -Uri "$base/chat/sessions/$($session.id)/messages" -Method POST `
        -Headers $headers -ContentType "application/json" -Body $msgBody -TimeoutSec 180
    $preview = $reply.message.content
    if ($preview.Length -gt 200) { $preview = $preview.Substring(0, 200) + "..." }
    Write-Host "   OK - resposta:" -ForegroundColor Green
    Write-Host "   $preview" -ForegroundColor Gray
    if ($reply.ragChunks -and @($reply.ragChunks).Count -gt 0) {
        Write-Host "   RAG chunks: $(@($reply.ragChunks).Count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ERRO no chat:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
    exit 1
}

Write-Host "5. Obter historico..." -ForegroundColor Cyan
try {
    $hist = Invoke-RestMethod -Uri "$base/chat/sessions/$($session.id)" -Headers $headers -TimeoutSec 15
    Write-Host "   OK - $($hist.messages.Count) mensagem(ns) na sessao" -ForegroundColor Green
} catch {
    Write-Host "   AVISO: nao foi possivel ler historico" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Fase 3 chat: OK" -ForegroundColor Green
