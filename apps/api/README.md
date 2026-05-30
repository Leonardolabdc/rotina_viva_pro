# Rotina Viva — worker FastAPI

API HTTP documentada em `packages/api-contracts/openapi.yaml`.

## Desenvolvimento local

**Fase 0** (só `/health` e stubs — instalação leve):

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_dev.py
```

**Fase 1** (Supabase Auth + listagem alunos):

```powershell
pip install -r requirements.txt -r requirements-supabase.txt
```

Requer `SUPABASE_URL`, `SUPABASE_ANON_KEY` e `SUPABASE_JWT_SECRET` no `.env` da raiz.

**Fase 3** (worker com lógica `src/` + ML/RAG + chat):

```powershell
pip install -r requirements-worker.txt
```

Guia completo: [docs/FASE3_FASTAPI.md](../../docs/FASE3_FASTAPI.md)

Recomendado: **Python 3.12** (ver `packages.toml` na raiz). Python 3.10 funciona para a Fase 0.

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Contrato YAML: http://localhost:8000/openapi.yaml

## Estado

| Rota | Estado |
|------|--------|
| `GET /health` | ✅ |
| `/auth/*`, `/students` | ✅ Fase 1 |
| `/chat/*` | ✅ Fase 3 (sync + SSE) |
| `/health` | ✅ inclui estado `llmGuard` (Fase 4) |
| `/reports/*`, `/transcribe`, `/direct-chat/*` | 501 — fases seguintes |

A lógica de negócio está em `../../src/` (`rotina_inference`, `api_chat_runner`).

## Produção (Fase 6)

```powershell
# Docker (raiz do repo)
docker compose -f docker-compose.prod.yml up --build -d

# Ou directamente
docker build -f apps/api/Dockerfile -t rotina-api .
docker run --env-file .env -p 8000:8000 rotina-api
```

- Entrypoint: `run_prod.py` (uvicorn, 1 worker)
- Railway: [`railway.toml`](railway.toml)
- Guia: [docs/FASE6_CUTOVER.md](../../docs/FASE6_CUTOVER.md)
