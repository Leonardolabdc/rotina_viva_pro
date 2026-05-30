# Fase 1 — Supabase (passo a passo)

Substituir **ficheiros locais** (CSV + JSON) por **Supabase**: Postgres, Auth, RLS e JSONB.

> O Streamlit continua a funcionar em paralelo até a Fase 3/6. A Fase 1 prepara o backend na nuvem.

---

## Visão geral (simples)

| Hoje (PoC) | Fase 1 (Supabase) |
|------------|-------------------|
| `rotina_users.json` | **Auth** (email/senha) + tabela `profiles` |
| `info_alunos.csv` | tabela `students` |
| `diario_estruturado.csv` | tabela `diary_entries` |
| ficheiros `.rotina_chat/` | tabela `chat_sessions` (JSONB) |
| regras no Python | **RLS** no Postgres |

---

## Passo 1 — Criar projecto Supabase

1. Entra em [supabase.com](https://supabase.com) → **New project**
2. Escolhe região próxima (ex.: South America)
3. Guarda a **database password**

Anota (Settings → API):

| Variável | Onde copiar |
|----------|-------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | anon public |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role (**secreto — só backend/scripts**) |
| `SUPABASE_JWT_SECRET` | JWT Settings → JWT Secret |

---

## Passo 2 — Aplicar schema (tabelas + RLS)

**Opção A — SQL Editor (mais simples)**

1. Supabase Dashboard → **SQL Editor** → New query
2. Cola o conteúdo de [`supabase/migrations/20260530120000_initial_schema.sql`](../supabase/migrations/20260530120000_initial_schema.sql)
3. **Run**

**Opção B — Supabase CLI**

```powershell
npm i -g supabase
supabase login
supabase link --project-ref SEU_PROJECT_REF
supabase db push
```

---

## Passo 3 — Configurar `.env`

Na raiz do repo, copia `.env.example` → `.env` e preenche:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=sua-jwt-secret
ROTINA_API_PHASE=1-supabase
```

---

## Passo 4 — Importar dados dos CSVs

```powershell
cd d:\Dev\rotina_viva_pro
pip install httpx pandas python-dotenv
python scripts/seed_supabase_from_csv.py
```

Importa `data/info_alunos.csv` → `students` e `data/diary_estruturado.csv` → `diary_entries`.

---

## Passo 5 — Criar utilizadores demo (Auth)

```powershell
python scripts/seed_supabase_demo_users.py
```

Cria contas equivalentes ao PoC:

| Email | Senha | Perfil |
|-------|-------|--------|
| `gestao.demo@rotinaviva.local` | `demo123` | gestão |
| `professor.demo@rotinaviva.local` | `demo123` | educador |
| `pai.demo@rotinaviva.local` | `demo123` | família (aluno id 1) |

> Em produção uses emails reais. `@rotinaviva.local` serve só para dev.

---

## Passo 6 — Testar Auth na API

```powershell
cd apps/api
pip install -r requirements.txt -r requirements-supabase.txt
python run_dev.py
```

**Login:**

```powershell
$body = @{ email = "gestao.demo@rotinaviva.local"; password = "demo123" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/auth/login -Method POST -ContentType "application/json" -Body $body
```

**Perfil (substitui TOKEN):**

```powershell
Invoke-RestMethod -Uri http://localhost:8000/auth/me -Headers @{ Authorization = "Bearer TOKEN" }
```

**Alunos:**

```powershell
Invoke-RestMethod -Uri http://localhost:8000/students -Headers @{ Authorization = "Bearer TOKEN" }
```

---

## Passo 7 — Storage (PDFs — preparação Fase 2)

1. Dashboard → **Storage** → New bucket → `rotina-documents` (privado)
2. Na Fase 2, os PDFs vão para este bucket; o RAG usará pgvector em vez de ChromaDB

---

## Checklist Fase 1

| # | Tarefa | OK? |
|---|--------|-----|
| 1 | Projecto Supabase criado | ⬜ |
| 2 | Migration SQL aplicada | ⬜ |
| 3 | `.env` com chaves | ⬜ |
| 4 | CSVs importados | ⬜ |
| 5 | Users demo criados | ⬜ |
| 6 | `POST /auth/login` → JWT | ⬜ |
| 7 | `GET /students` com RLS | ⬜ |

---

## O que **não** muda ainda

- **Streamlit** (`app.py`) — continua DuckDB/CSV local
- **Chat IA / RAG** — Fases 2–3
- **Next.js** — Fase 5

A Fase 1 coloca a **base de dados e login** prontos; a Fase 3 liga o motor `src/` a este Postgres.

---

## Referências

- Schema: [`supabase/migrations/`](../supabase/migrations/)
- Contrato API: [`packages/api-contracts/openapi.yaml`](../packages/api-contracts/openapi.yaml)
- Monorepo: [MONOREPO.md](MONOREPO.md)
