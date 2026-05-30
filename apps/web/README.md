# apps/web — Next.js (Fase 5)

Frontend profissional na Vercel, consumindo o worker FastAPI.

## Desenvolvimento local

**Pré-requisitos:** API a correr em `:8000` (ver [FASE3_FASTAPI.md](../../docs/FASE3_FASTAPI.md)).

```powershell
# Terminal 1 — API
cd d:\Dev\rotina_viva_pro
.\scripts\start_api_dev.ps1

# Terminal 2 — Web
cd d:\Dev\rotina_viva_pro
.\scripts\start_web_dev.ps1
```

Abrir http://localhost:3000 → login `gestao.demo` / `demo123`.

## Variáveis

| Variável | Descrição |
|----------|-----------|
| `NEXT_PUBLIC_ROTINA_API_URL` | Base da API (default `http://127.0.0.1:8000`) |

Copie `.env.local.example` → `.env.local`.

Na API, CORS aceita `:3000` por defeito. Para Vercel, defina `ROTINA_CORS_ORIGINS` no worker.

## Stack

- Next.js 15 (App Router)
- Tailwind CSS 4
- Auth via `POST /auth/login` (Supabase por trás da API)
- Chat via SSE `POST /chat/sessions/{id}/messages/stream`

## Contrato

Rotas e schemas em [`packages/api-contracts`](../../packages/api-contracts/openapi.yaml).

Guia completo: [docs/FASE5_NEXTJS.md](../../docs/FASE5_NEXTJS.md)
