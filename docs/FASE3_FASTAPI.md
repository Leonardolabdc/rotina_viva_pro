# Fase 3 — FastAPI worker (chat real)

Guia para correr o **motor de chat** (`src/`) via API HTTP, com sessões persistidas no Supabase.

> **Pré-requisitos:** Fase 1 (Supabase + auth) e Fase 2 (pgvector opcional mas recomendado).

---

## O que muda

| Antes | Fase 3 |
|-------|--------|
| Rotas `/chat/*` → 501 | Chat funcional (sync + SSE) |
| Histórico em ficheiros `.rotina_chat/` | Tabela `chat_sessions` (JSONB) |
| Só Streamlit | **FastAPI** reutiliza `rotina_inference` + guardrails |

Dados estruturados (cadastro/diário) continuam nos **CSVs locais** via DuckDB até migração completa para Postgres — igual ao PoC.

---

## Passo 1 — Dependências do worker

```powershell
cd d:\Dev\rotina_viva_pro\apps\api
pip install -r requirements-worker.txt
```

Isto instala FastAPI + stack ML/RAG do PoC (`requirements-prod.txt`).

---

## Passo 2 — `.env` na raiz do repo

```env
ROTINA_API_PHASE=3-fastapi-worker
ROTINA_RAG_BACKEND=pgvector

# Supabase (Fase 1)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...

# OpenRouter (LLM + embeddings)
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=meta-llama/llama-3.3-70b-instruct
```

CSVs em `data/` (`info_alunos.csv`, `diario_estruturado.csv`) e PDFs para RAG.

---

## Passo 3 — Arrancar API

```powershell
cd apps\api
python run_dev.py
```

Verificar:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
# phase: "3-fastapi-worker" (se worker deps instaladas)
```

Documentação interactiva: http://127.0.0.1:8000/docs

---

## Passo 4 — Teste automatizado

```powershell
cd d:\Dev\rotina_viva_pro
.\scripts\test_api_chat.ps1
```

Fluxo: login → criar sessão → pergunta sobre alunos → (opcional) pergunta RAG cardápio.

---

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat/sessions` | Nova sessão |
| GET | `/chat/sessions/{id}` | Histórico |
| POST | `/chat/sessions/{id}/messages` | Resposta síncrona |
| POST | `/chat/sessions/{id}/messages/stream` | SSE (`status`, `token`, `done`, `error`) |

Autenticação: `Authorization: Bearer <JWT>` (login em `/auth/login`).

---

## Exemplo manual (PowerShell)

```powershell
$base = "http://127.0.0.1:8000"
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" `
  -Body (@{ username = "gestao.demo"; password = "demo123" } | ConvertTo-Json)
$token = $login.accessToken

$session = Invoke-RestMethod -Uri "$base/chat/sessions" -Method POST `
  -Headers @{ Authorization = "Bearer $token" } -ContentType "application/json" -Body "{}"

$reply = Invoke-RestMethod -Uri "$base/chat/sessions/$($session.id)/messages" -Method POST `
  -Headers @{ Authorization = "Bearer $token" } -ContentType "application/json" `
  -Body (@{ content = "Quantos alunos temos cadastrados?" } | ConvertTo-Json)

$reply.message.content
```

---

## Mutações CSV (gestão)

DELETE ou UPDATE em massa exige confirmação — reenvie com `"confirmMutation": true`:

```json
{
  "content": "apague o aluno X",
  "confirmMutation": true
}
```

Perfil **educador**: INSERT/UPDATE permitidos; DELETE bloqueado.  
Perfil **família**: só leitura.

---

## Arquitectura

```
apps/api/rotina_api/routers/chat.py   → HTTP
apps/api/rotina_api/chat_store.py     → Supabase chat_sessions
src/modules/api_chat_runner.py        → quota + RBAC + orquestração
src/modules/rotina_inference.py       → plano, SQL, RAG, streaming
```

---

## Limitações (MVP Fase 3)

- Relatórios (`/reports/*`), transcrição e chat directo família ↔ educador ainda 501
- CrewAI opcional (`crewAiEnabled: true` na sessão)
- CSVs locais (não Postgres) para cadastro/diário
- LLM Guard dedicado fica para Fase 4

---

## Próximo passo

**Fase 4** — LLM Guard no worker + hardening.  
**Fase 5** — frontend Next.js na Vercel.
