# Fase 7 — Cadastro e diário no Supabase (fonte única)

Migrar o motor de chat de **CSV/DuckDB** para **Postgres (Supabase)** mantendo o mesmo SQL (`info_alunos`, `diario_estruturado`) via **views**.

**Pré-requisitos:** Fases 1–2 (schema + pgvector), dados importados.

---

## O que muda

| Antes | Depois (`ROTINA_DATA_BACKEND=supabase`) |
|-------|----------------------------------------|
| Chat lê/grava CSV em `/data` | Chat lê/grava `students` + `diary_entries` |
| Volume Railway opcional | **Sem volume** para cadastro (só Supabase) |
| `GET /students` vs chat divergiam | **Mesma fonte** |

Auth, sessões chat e RAG pgvector **já estavam** no Supabase.

---

## Passo 1 — Migration (SQL Editor)

Correr no Supabase (depois das migrations iniciais):

1. [`supabase/migrations/20260531120000_csv_compat_views.sql`](../supabase/migrations/20260531120000_csv_compat_views.sql)

Cria views `info_alunos` e `diario_estruturado` + triggers INSERT/UPDATE/DELETE.

---

## Passo 2 — Importar dados demo (se vazio)

```powershell
cd d:\Dev\rotina_viva_pro
python scripts/seed_supabase_from_csv.py
python scripts/seed_supabase_demo_users.py
```

Confirme no Table Editor: **120** linhas em `students`.

---

## Passo 3 — Variáveis (Railway → serviço `api`)

```env
ROTINA_DATA_BACKEND=supabase
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Obter **DATABASE_URL**: Supabase → **Connect** → **Transaction pooler** (porta **6543**).

Se a URI tiver `?pgbouncer=true`, **remova** esse sufixo no Railway (psycopg não aceita) — ou use deploy recente do worker que remove automaticamente.

Manter:

```env
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_JWT_SECRET=...
ROTINA_RAG_BACKEND=pgvector
```

**Não** expor `DATABASE_URL` na Vercel — só no worker Railway.

---

## Passo 4 — Redeploy e verificar

```http
GET https://SUA-API.railway.app/health
```

```json
"structuredData": {
  "backend": "supabase",
  "postgresConfigured": true,
  "ready": true
}
```

Teste chat (Gestão): *quantos alunos tem na turma infantil 2?* → **47**

---

## Desenvolvimento local

**CSV (default)** — sem `ROTINA_DATA_BACKEND` ou `=csv`:

```powershell
.\scripts\start_api_dev.ps1
```

**Supabase local** — no `.env`:

```env
ROTINA_DATA_BACKEND=supabase
DATABASE_URL=postgresql://...
```

---

## Rollback

Railway → remover `ROTINA_DATA_BACKEND` ou `ROTINA_DATA_BACKEND=csv` + volume `/data` (ver [PERSISTENCIA_RAILWAY.md](PERSISTENCIA_RAILWAY.md)).

---

## Limitações conhecidas (v1)

- Streamlit legado: continua a preferir CSV local salvo config Supabase no `.env`.
- SQL muito específico de DuckDB pode falhar — reportar; views cobrem o fluxo actual.
- Backups de mutação: audit em ficheiro local desactivado em modo Supabase (dados no Postgres).

---

Ver também: [FASE1_SUPABASE.md](FASE1_SUPABASE.md) · [PERSISTENCIA_RAILWAY.md](PERSISTENCIA_RAILWAY.md) · [TESTES_PRODUCAO.md](TESTES_PRODUCAO.md)
