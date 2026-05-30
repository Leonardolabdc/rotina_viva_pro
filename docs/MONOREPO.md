# Monorepo — Rotina Viva Pro

Estrutura introduzida na **Fase 0** do roadmap de migração.

## Layout

```
rotina_viva_pro/
├── apps/
│   ├── api/                 # FastAPI worker (Fase 3)
│   └── web/                 # Next.js na Vercel (Fase 5)
├── packages/
│   └── api-contracts/       # OpenAPI 3.1 — fonte da verdade HTTP
├── src/                     # Lógica Python herdada do PoC (CrewAI, RAG, guardrails)
├── app.py                   # Streamlit legado (até Fase 6)
├── data/                    # CSVs / Chroma local (até Fase 1–2)
└── docs/
```

## Princípios

1. **`packages/api-contracts/openapi.yaml`** define rotas, schemas e RBAC antes da implementação.
2. **`src/`** permanece a biblioteca de domínio; `apps/api` expõe HTTP sem duplicar regras.
3. **Streamlit** continua funcional em Docker até cutover (Fase 6).

## Comandos (raiz)

```powershell
pnpm install
pnpm contracts:validate
pnpm contracts:generate
pnpm dev:api          # FastAPI em :8000
```

Streamlit (legado):

```powershell
docker compose up --build -d    # :8501
```

## Mapa fases → pastas

| Fase | Entregável | Onde |
|------|------------|------|
| 0 | Monorepo + contrato | `apps/`, `packages/api-contracts` |
| 1 | Supabase Auth + Postgres | migrations, RLS; auth em `apps/api` |
| 2 | pgvector RAG | substituir `src/modules/rag_index.py` |
| 3 | FastAPI completo | `apps/api/rotina_api/` → chama `src/` |
| 4 | LLM Guard | middleware no worker |
| 5 | Next.js | `apps/web/` |
| 6 | Cutover | desligar `app.py` do deploy |

## Referências

- Contrato: [packages/api-contracts/openapi.yaml](../packages/api-contracts/openapi.yaml)
- Arquitectura PoC: [ARQUITETURA.md](ARQUITETURA.md)
- Roadmap: [README.md](../README.md)
