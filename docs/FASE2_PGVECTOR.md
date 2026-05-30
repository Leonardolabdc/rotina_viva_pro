# Fase 2 — pgvector (RAG na nuvem)

Guia passo a passo para substituir ChromaDB local por **pgvector no Supabase**.

> **Pré-requisito:** Fase 1 concluída (projecto Supabase + `.env` com chaves).

---

## O que muda

| Antes (PoC) | Fase 2 |
|-------------|--------|
| ChromaDB em `data/vector_db/` | Tabela `document_chunks` + pgvector |
| Embeddings locais/API → Chroma | Mesmos embeddings → **Supabase** |
| Só no Docker/PC | Index na **nuvem** (partilhado pela API) |

---

## Passo 1 — Activar extensão vector

Supabase Dashboard → **Database** → **Extensions** → procurar **vector** → Enable.

---

## Passo 2 — Aplicar migration SQL

SQL Editor → colar [`supabase/migrations/20260530200000_pgvector_rag.sql`](../supabase/migrations/20260530200000_pgvector_rag.sql) → **Run**.

Tabelas criadas:
- `document_chunks` — trechos + embedding `vector(1536)`
- `rag_index_meta` — fingerprint dos PDFs
- função `match_document_chunks` — busca por similaridade

---

## Passo 3 — `.env`

```env
ROTINA_RAG_BACKEND=pgvector
# OPENAI_EMBED_DIMENSIONS=1536   # deve coincidir com a migration (default 1536)
```

Mantém as chaves Supabase da Fase 1 e as chaves OpenRouter para embeddings.

---

## Passo 4 — PDFs em `data/`

Coloca os PDFs institucionais (mesmos nomes do PoC):

- `regimento_interno_escola.pdf`
- `planejamento_nutricional_semanal.pdf`
- `guia_procedimentos_saude_seguranca.pdf`
- `ppp_projeto_político_pedagógico.pdf`

---

## Passo 5 — Indexar (consome tokens OpenRouter)

```powershell
cd d:\Dev\rotina_viva_pro
pip install httpx python-dotenv chromadb pypdf  # chromadb só para embedding function
python scripts/build_rag_pgvector.py
```

Demora alguns minutos na 1.ª vez (embeddings via API).

---

## Passo 6 — Testar busca

```powershell
python scripts/query_rag_pgvector.py "Qual o cardápio da semana?"
```

---

## Passo 7 — Streamlit com pgvector (opcional)

No `.env`:

```env
ROTINA_RAG_BACKEND=pgvector
```

Reinicia o Docker Streamlit — o app usa `get_chroma_collection()` que delega ao pgvector **sem alterar a UI**.

Para voltar ao Chroma local:

```env
ROTINA_RAG_BACKEND=chroma
```

---

## Checklist Fase 2

| # | Tarefa | OK? |
|---|--------|-----|
| 1 | Extensão `vector` activa | ⬜ |
| 2 | Migration SQL aplicada | ⬜ |
| 3 | PDFs em `data/` | ⬜ |
| 4 | `build_rag_pgvector.py` OK | ⬜ |
| 5 | `query_rag_pgvector.py` devolve trechos | ⬜ |

---

## Notas

- Dimensão do vector: **1536** (`text-embedding-3-small`). Se mudar modelo, actualiza a migration.
- Ingestão usa **service_role**; leitura na app usa RLS (`authenticated`) ou service role no backend.
- Fase 3 ligará o chat FastAPI a este RAG; Fase 2 prepara o índice na nuvem.
