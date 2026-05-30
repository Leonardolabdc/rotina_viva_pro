# Deploy de produção — Rotina Viva Pro

Stack alvo após **Fase 6** (cutover).

| Camada | Onde | Guia |
|--------|------|------|
| Frontend | **Vercel** (`apps/web`) | [FASE5_NEXTJS.md](FASE5_NEXTJS.md) |
| API / IA | **Railway, Fly.io ou VPS** | este doc |
| Auth + DB + RAG | **Supabase** | [FASE1_SUPABASE.md](FASE1_SUPABASE.md) |
| LLM Guard | No worker | [FASE4_LLM_GUARD.md](FASE4_LLM_GUARD.md) |

> Streamlit Cloud: ver [DEPLOY.md](DEPLOY.md) — **legado**, não usar para este repo.

---

## 1. Supabase

Schema e seeds já documentados em [FASE1_SUPABASE.md](FASE1_SUPABASE.md).

Variáveis obrigatórias no worker:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=...
ROTINA_RAG_BACKEND=pgvector
```

Indexar RAG: `python scripts/build_rag_pgvector.py`

---

## 2. Worker FastAPI

### Opção A — Docker (VPS)

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Porta `8000`. Health: `GET /health`

### Opção B — Railway

- Dockerfile: `apps/api/Dockerfile`
- Build context: raiz do repo
- Port: `8000`
- Memória: **≥4 GB** com LLM Guard

### Variáveis mínimas

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=meta-llama/llama-3.3-70b-instruct
ROTINA_API_PHASE=4-llm-guard
ROTINA_LLM_GUARD_ENABLED=true
ROTINA_CORS_ORIGINS=https://SEU-APP.vercel.app
PORT=8000
```

---

## 3. Vercel (frontend)

- **Root Directory:** `apps/web`
- **Env:** `NEXT_PUBLIC_ROTINA_API_URL=https://URL-DO-WORKER`

Build: `npm run build` (automático)

---

## 4. Ordem de deploy

1. Supabase migrations + seeds + RAG pgvector
2. Worker → confirmar `/health`
3. Vercel → apontar para URL do worker
4. Testar login + chat em produção

---

## 5. Streamlit legado (opcional, local)

```powershell
docker compose -f docker-compose.legacy.yml up -d
```

Não expor `:8501` na internet em produção.

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| CORS no browser | Adicionar URL Vercel em `ROTINA_CORS_ORIGINS` |
| OOM / worker morre | Desligar LLM Guard ou aumentar RAM |
| Chat 500 | Logs do worker; confirmar Supabase + OpenRouter |
| Login falha | Users demo: `scripts/seed_supabase_demo_users.py` |

Guia completo cutover: [FASE6_CUTOVER.md](FASE6_CUTOVER.md)
