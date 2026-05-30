# Passo a passo — produção completa (Supabase + Railway + Vercel)

Guia prático para colocar **Rotina Viva Pro** no ar depois das Fases 0–6.

**Stack final:**

```
Browser → Vercel (Next.js) → Railway (FastAPI) → Supabase + OpenRouter
```

**Tempo estimado:** 1–2 h (primeira vez).

---

## Contas necessárias

| Serviço | Para quê | Plano grátis |
|---------|----------|--------------|
| [Supabase](https://supabase.com) | Auth, Postgres, pgvector | Sim |
| [OpenRouter](https://openrouter.ai) | Chat + embeddings | Pay-per-use |
| [Railway](https://railway.app) | API worker Python | Trial / Hobby |
| [Vercel](https://vercel.com) | Frontend Next.js | Hobby |
| [GitHub](https://github.com) | Repo `rotina_viva_pro` | Sim |

---

## Parte A — Supabase (já feito localmente?)

Se **já testaste** login `gestao.demo` no PC, o Supabase está OK. Confirma só:

### A1. Projecto activo

Dashboard Supabase → **Settings → API** — anota:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_JWT_SECRET` (JWT Settings)
- `SUPABASE_SERVICE_ROLE_KEY` (só scripts — **nunca** na Vercel)

### A2. Schema aplicado

SQL Editor → colar e correr (se ainda não correste):

1. `supabase/migrations/20260530120000_initial_schema.sql`
2. `supabase/migrations/20260530200000_pgvector_rag.sql`

### A3. Dados e utilizadores demo

No PC, na raiz do repo:

```powershell
cd d:\Dev\rotina_viva_pro
pip install httpx pandas python-dotenv
python scripts/seed_supabase_from_csv.py
python scripts/seed_supabase_demo_users.py
```

Utilizadores criados:

| Login | Senha | Perfil |
|-------|-------|--------|
| `gestao.demo` | `demo123` | gestão |
| `professor.demo` | `demo123` | educador |
| `pai.demo` | `demo123` | família |

### A4. Índice RAG (pgvector)

```powershell
python scripts/build_rag_pgvector.py
```

Sem isto, perguntas sobre regimento/PDFs falham em produção.

---

## Parte B — Railway (API worker)

### B1. Criar projecto

1. [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub repo** → escolhe `Leonardolabdc/rotina_viva_pro`
3. Branch: `main`

### B2. Configurar build (crítico — monorepo)

Railway importa monorepos e **erroneamente** põe `pnpm --filter @rotina-viva/api dev`. A API é **Python/Docker**, não pnpm.

No serviço **`rotina-viva/api` → Settings**:

| Campo | Valor correcto |
|-------|----------------|
| **Root Directory** | `/` (vazio = raiz do repo) — **NÃO** `apps/api` |
| **Builder** | Dockerfile |
| **Dockerfile path** | `apps/api/Dockerfile` |
| **Custom Start Command** | **Apagar / deixar vazio** (usa `python run_prod.py` do Dockerfile) |
| **Config-as-code** | `/apps/api/railway.toml` (opcional, já no repo) |

Se **Root Directory** = `apps/api`, o build falha em ~2 s (`COPY requirements-prod.txt` não encontrado).

Apaga o serviço **`rotina-viva/web`** no Railway (frontend fica na Vercel) ou desliga deploy dele.

### B3. Variáveis de ambiente (Railway → Service → Variables)

Copia do teu `.env` local. **Lista mínima:**

```env
# Supabase
SUPABASE_URL=https://SEU_PROJECT.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=sua-jwt-secret
SUPABASE_DEMO_EMAIL_DOMAIN=rotinaviva.local

# Fase / RAG
ROTINA_API_PHASE=4-llm-guard
ROTINA_RAG_BACKEND=pgvector
OPENAI_EMBED_DIMENSIONS=1536

# OpenRouter
ROTINA_CHAT_PROVIDER=openrouter
ROTINA_EMBED_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=meta-llama/llama-3.3-70b-instruct
OPENAI_EMBED_MODEL=openai/text-embedding-3-small
OPENROUTER_HTTP_REFERER=https://github.com/Leonardolabdc/rotina_viva_pro
OPENROUTER_APP_TITLE=Rotina Viva

# Worker
PORT=8000
ROTINA_DATA_DIR=/data
ROTINA_ENABLE_CREWAI=false
ROTINA_ENABLE_ML_LAB=false
ROTINA_LANGFUSE_ENABLED=false

# CORS — preenche DEPOIS de ter URL Vercel (Parte C)
ROTINA_CORS_ORIGINS=https://SEU-APP.vercel.app,http://localhost:3000
```

#### LLM Guard (importante)

| Plano Railway | Recomendação |
|---------------|--------------|
| Hobby / pouca RAM | `ROTINA_LLM_GUARD_ENABLED=false` (só rule-based) |
| ≥ 4 GB RAM | `ROTINA_LLM_GUARD_ENABLED=true` |

Para **primeiro deploy**, usa `false` — sobe mais rápido e evita OOM. Activa depois.

```env
ROTINA_LLM_GUARD_ENABLED=false
ROTINA_LLM_GUARD_FAIL_OPEN=true
```

#### Voz (opcional)

Sem Whisper no Railway, usa OpenRouter STT:

```env
OPENAI_TRANSCRIBE_BASE_URL=https://openrouter.ai/api/v1
OPENAI_TRANSCRIBE_MODEL=openai/whisper-1
```

### B4. Rede pública

Railway → Service → **Settings → Networking → Generate Domain**

Anote a URL, ex.: `https://rotina-api-production-xxxx.up.railway.app`

### B5. Testar worker

No browser ou PowerShell:

```powershell
Invoke-RestMethod https://SUA-URL-RAILWAY.app/health
```

Esperado:

```json
{
  "status": "ok",
  "phase": "3-fastapi-worker",
  "supabase": "configured",
  "llmGuard": { "active": false }
}
```

Teste login:

```powershell
$body = @{ username = "gestao.demo"; password = "demo123" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://SUA-URL-RAILWAY.app/auth/login" -Method POST -ContentType "application/json" -Body $body
```

Deve devolver `accessToken` e `user.role = gestao`.

> **Build demora** 10–20 min na 1.ª vez (PyTorch se LLM Guard activo).

---

## Parte C — Vercel (frontend Next.js)

### C1. Importar repo

1. [vercel.com/new](https://vercel.com/new)
2. Import `Leonardolabdc/rotina_viva_pro`
3. **Root Directory:** clica *Edit* → `apps/web`

### C2. Environment Variables

| Nome | Valor |
|------|-------|
| `NEXT_PUBLIC_ROTINA_API_URL` | `https://SUA-URL-RAILWAY.app` (sem `/` no fim) |

**Não** coloques `OPENROUTER_API_KEY` nem `SUPABASE_SERVICE_ROLE_KEY` na Vercel — ficam só no Railway.

### C3. Deploy

Clica **Deploy**. URL exemplo: `https://rotina-viva-pro.vercel.app`

### C4. Actualizar CORS no Railway

Volta ao Railway → Variables:

```env
ROTINA_CORS_ORIGINS=https://rotina-viva-pro.vercel.app,http://localhost:3000
```

(use a URL **exacta** da Vercel, com `https://`)

Railway faz **redeploy** automático.

---

## Parte D — Teste final em produção

1. Abre `https://SEU-APP.vercel.app`
2. Login: `gestao.demo` / `demo123`
3. Pergunta: *Quantos alunos temos no cadastro? Responda em uma frase.*
4. Deves ver resposta com **120 alunos** (streaming)

Checklist:

- [ ] Login OK
- [ ] Chat responde
- [ ] Segunda pergunta funciona
- [ ] `/health` do Railway OK
- [ ] Sem erro CORS na consola do browser (F12 → Network)

---

## Problemas comuns

### "Falha ao comunicar com a API" / CORS

- Confirma `NEXT_PUBLIC_ROTINA_API_URL` na Vercel
- Confirma `ROTINA_CORS_ORIGINS` inclui URL **exacta** da Vercel
- Redeploy Railway após mudar CORS

### Login 401

- Correr `seed_supabase_demo_users.py`
- Verificar `SUPABASE_JWT_SECRET` no Railway

### Worker reinicia / 502

- RAM insuficiente → `ROTINA_LLM_GUARD_ENABLED=false`
- Ver **Logs** no Railway

### Chat lento

- Normal com LLM Guard em CPU
- Normal na 1.ª pergunta (cold start)

### Build Railway falha em 2 segundos

- **Root Directory** está em `apps/api` → mudar para **raiz `/`**
- **Start command** = `pnpm ...` → **apagar**
- Ver Build Logs: `COPY failed` = contexto Docker errado

### Build Railway falha ao instalar pacotes (OOM)

- Logs → falta variável ou timeout no pip
- Tenta deploy sem LLM Guard primeiro

---

## Ordem resumida (cola no Notion)

```
1. Supabase OK + seeds + RAG pgvector
2. Railway: repo + variables + domain
3. Testar /health e /auth/login no Railway
4. Vercel: apps/web + NEXT_PUBLIC_ROTINA_API_URL
5. Railway: ROTINA_CORS_ORIGINS = URL Vercel
6. Testar login + chat na Vercel
7. (Opcional) LLM Guard true + plano com mais RAM
```

---

## Desenvolvimento local (continua igual)

```powershell
# Terminal 1
.\scripts\start_api_dev.ps1

# Terminal 2
.\scripts\start_web_dev.ps1
```

---

## Referências

- [FASE1_SUPABASE.md](FASE1_SUPABASE.md)
- [FASE6_CUTOVER.md](FASE6_CUTOVER.md)
- [DEPLOY_PROD.md](DEPLOY_PROD.md)
