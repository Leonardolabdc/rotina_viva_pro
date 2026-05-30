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

**Fase 3+** (worker com lógica `src/` + ML/RAG):

```powershell
pip install -r requirements-worker.txt
```

Recomendado: **Python 3.12** (ver `packages.toml` na raiz). Python 3.10 funciona para a Fase 0.

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Contrato YAML: http://localhost:8000/openapi.yaml

## Estado (Fase 0)

| Rota | Estado |
|------|--------|
| `GET /health` | ✅ Implementada |
| Demais rotas | 501 — stubs alinhados ao contrato |

A lógica de negócio permanece em `../../src/` até a Fase 3.
