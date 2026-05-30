# Fase 6 — Cutover (stack de produção)

Migração do **Streamlit** como deploy principal para **Next.js (Vercel) + FastAPI worker**.

> **Pré-requisito:** Fases 1–5 concluídas e testadas localmente.

---

## O que mudou

| Antes | Depois |
|-------|--------|
| `docker-compose.prod.yml` → Streamlit :8501 | `docker-compose.prod.yml` → **API worker :8000** |
| Deploy público = Streamlit Cloud | Frontend = **Vercel** (`apps/web`) |
| UI monolítica | UI Next.js + worker HTTP |

**Streamlit** permanece no repo para referência e dev local:

```powershell
docker compose -f docker-compose.legacy.yml up --build -d
# http://localhost:8501
```

---

## Stack de produção

```
Utilizador
  → Next.js (Vercel)
  → FastAPI worker (Railway / Fly / VPS / Docker)
  → Supabase (Auth, Postgres, pgvector)
  → OpenRouter (LLM)
```

---

## Passo 1 — Worker Docker (VPS ou teste local)

```powershell
cd d:\Dev\rotina_viva_pro
copy .env.example .env
# Preencher Supabase, OpenRouter, ROTINA_LLM_GUARD_ENABLED, etc.

docker compose -f docker-compose.prod.yml up --build -d
curl http://127.0.0.1:8000/health
```

Script Windows:

```powershell
.\scripts\start_prod_docker.ps1
```

**RAM:** recomendado **≥4 GB** se `ROTINA_LLM_GUARD_ENABLED=true`.

---

## Passo 2 — Frontend Vercel

1. [vercel.com](https://vercel.com) → Import → repo `rotina_viva_pro`
2. **Root Directory:** `apps/web`
3. **Environment:**
   ```env
   NEXT_PUBLIC_ROTINA_API_URL=https://sua-api.railway.app
   ```
4. Deploy

---

## Passo 3 — CORS e secrets no worker

No painel Railway/Fly ou `.env` do Docker:

```env
ROTINA_CORS_ORIGINS=https://seu-app.vercel.app,http://localhost:3000
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_JWT_SECRET=...
OPENROUTER_API_KEY=...
ROTINA_RAG_BACKEND=pgvector
ROTINA_LLM_GUARD_ENABLED=true
```

Reinicie o worker após alterar CORS.

---

## Passo 4 — Checklist pós-cutover

- [ ] `/health` → `phase: 4-llm-guard` (ou `3-fastapi-worker` se ML off)
- [ ] Login Next.js com `gestao.demo`
- [ ] Chat SSE responde
- [ ] Streamlit **não** exposto publicamente
- [ ] Secrets só no worker (nunca `SERVICE_ROLE` no frontend)

---

## Railway (worker)

Ficheiro [`apps/api/railway.toml`](../apps/api/railway.toml) aponta para o Dockerfile.

1. New Project → Deploy from GitHub
2. Root: repo completo
3. Variables: copiar do `.env`
4. Copiar URL pública → `NEXT_PUBLIC_ROTINA_API_URL` na Vercel

---

## Ficheiros relevantes

| Ficheiro | Função |
|----------|--------|
| `apps/api/Dockerfile` | Imagem worker |
| `apps/api/run_prod.py` | Uvicorn produção (1 worker) |
| `docker-compose.prod.yml` | Stack nova |
| `docker-compose.legacy.yml` | Streamlit legado |
| `docs/DEPLOY_PROD.md` | Guia deploy resumido |

---

## Repositório académico

O PoC CBL permanece em [**Rotina-Viva**](https://github.com/Leonardolabdc/Rotina-Viva) — **congelado** para avaliação. Este repo (`rotina_viva_pro`) é a evolução de produção.
