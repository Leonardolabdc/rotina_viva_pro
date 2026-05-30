# Rotina Viva — worker FastAPI

API HTTP documentada em `packages/api-contracts/openapi.yaml`.

## Desenvolvimento local

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_dev.py
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Contrato YAML: http://localhost:8000/openapi.yaml

## Estado (Fase 0)

| Rota | Estado |
|------|--------|
| `GET /health` | ✅ Implementada |
| Demais rotas | 501 — stubs alinhados ao contrato |

A lógica de negócio permanece em `../../src/` até a Fase 3.
