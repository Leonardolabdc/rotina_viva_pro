# Fase 5 — Next.js na Vercel

Frontend profissional que consome o worker FastAPI (Fases 3–4) via contrato OpenAPI.

> **Pré-requisito:** Fases 1–4 operacionais localmente (Supabase + API + opcional LLM Guard).

---

## O que foi entregue

| Peça | Descrição |
|------|-----------|
| `apps/web/` | Next.js 15, App Router, Tailwind |
| Login | `POST /auth/login` — utilizadores demo Supabase |
| Chat | SSE em `/chat/sessions/{id}/messages/stream` |
| CORS | `ROTINA_CORS_ORIGINS` no worker para domínio Vercel |

---

## Passo 1 — Dependências

Na raiz do monorepo (Node ≥ 20):

```powershell
cd d:\Dev\rotina_viva_pro
npm install
```

Ou, se tiver `pnpm`:

```powershell
pnpm install
```

---

## Passo 2 — Configurar frontend

```powershell
cd apps\web
copy .env.local.example .env.local
```

Conteúdo típico:

```env
NEXT_PUBLIC_ROTINA_API_URL=http://127.0.0.1:8000
```

---

## Passo 3 — Correr localmente

**Terminal 1 — API:**

```powershell
cd d:\Dev\rotina_viva_pro
.\scripts\start_api_dev.ps1
```

**Terminal 2 — Web:**

```powershell
cd d:\Dev\rotina_viva_pro
.\scripts\start_web_dev.ps1
```

Abrir http://localhost:3000

| Utilizador | Palavra-passe | Perfil |
|------------|---------------|--------|
| `gestao.demo` | `demo123` | gestão |
| `professor.demo` | `demo123` | educador |
| `pai.demo` | `demo123` | família |

---

## Passo 4 — Teste rápido

1. Login com `gestao.demo`
2. Enviar: *Quantos alunos temos no cadastro?*
3. Ver tokens a aparecer em streaming
4. Botão **Nova sessão** limpa histórico local

---

## Deploy Vercel (Hobby)

1. [vercel.com](https://vercel.com) → Import GitHub → repo `rotina_viva_pro`
2. **Root Directory:** `apps/web`
3. **Environment variables:**
   - `NEXT_PUBLIC_ROTINA_API_URL` = URL pública do worker (Railway/Fly — ainda a configurar)
4. Deploy

> O frontend **não** embute LLM Guard nem OpenRouter — tudo passa pela API.

---

## CORS no worker (obrigatório em produção)

No `.env` do worker FastAPI:

```env
ROTINA_CORS_ORIGINS=http://localhost:3000,https://seu-app.vercel.app
```

Reinicie a API após alterar.

---

## Arquitectura

```
Browser (Next.js :3000)
  → POST /auth/login
  → POST /chat/sessions
  → POST /chat/sessions/{id}/messages/stream (SSE)
       ↓
FastAPI worker (:8000)
  → guardrails + LLM Guard
  → src/ (RAG, SQL, OpenRouter)
  → Supabase (sessões, perfis)
```

---

## Próximo passo

Roadmap concluído (Fases 0–6). Deploy: [DEPLOY_PROD.md](../../docs/DEPLOY_PROD.md).
