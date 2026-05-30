# Persistência de dados (CSV) — Railway

Por defeito, o disco do contentor Railway é **efémero**: cada redeploy repõe a imagem Docker e **apaga** alterações feitas via chat (INSERT/UPDATE/DELETE nos CSV).

Este guia activa um **Volume Railway** em `/data` para persistir:

- `info_alunos.csv`
- `diario_estruturado.csv`
- backups automáticos (`.rotina_backups/`)
- quota LLM (`.rotina_usage/`)

**Auth, sessões de chat e RAG** já vivem no **Supabase** — não dependem deste volume.

---

## Como funciona no código

| Caminho | Função |
|---------|--------|
| `/app/seed-data` | CSVs demo **dentro da imagem** (só leitura) |
| `/data` | `ROTINA_DATA_DIR` — disco de runtime (volume) |
| Arranque | `ensure_persistent_data_dir()` copia seed → `/data` **só se** `info_alunos.csv` não existir |

Mutations via Gestão gravam em `/data` com `persist_duckdb_tables_to_csv()`.

---

## Passo 1 — Volume no Railway

1. [railway.app](https://railway.app) → projecto → serviço **`rotina-viva/api`**
2. **Settings** → **Volumes** → **Add Volume**
3. **Mount path:** `/data` (exactamente — coincide com `ROTINA_DATA_DIR` no Dockerfile)
4. Guardar → **Redeploy** do serviço

**CLI (alternativa):**

```bash
railway link
railway volume add --mount-path /data
```

---

## Passo 2 — Variáveis (confirmar)

No serviço **api**, já deve existir:

```env
ROTINA_DATA_DIR=/data
```

Não é necessário definir `ROTINA_SEED_DATA_DIR` — a imagem define `/app/seed-data`.

---

## Passo 3 — Verificar

Após redeploy:

```text
GET https://SUA-URL-RAILWAY.app/health
```

Procure `"dataDir"`:

```json
"dataDir": {
  "path": "/data",
  "writable": true,
  "infoAlunosCsv": true,
  "diarioCsv": true,
  "seededFiles": ["info_alunos.csv", "diario_estruturado.csv", ...]
}
```

| Campo | Significado |
|-------|-------------|
| `writable: true` | Volume montado e gravável |
| `infoAlunosCsv: true` | Cadastro pronto |
| `seededFiles` non-empty | 1.º arranque copiou demo do seed (normal) |
| `seededFiles: []` | Volume já tinha dados — **não sobrescreveu** |

---

## Passo 4 — Teste de mutação (opcional, 1 LLM)

Com **gestao.demo**:

1. Pergunta de leitura: *quantos alunos tem na turma infantil 2?* → 47
2. Pedido de alteração simples (se quiser gastar 1 crédito): ex. actualizar recado no diário
3. **Redeploy** manual no Railway
4. Repetir a mesma pergunta — o dado alterado **deve manter-se**

Sem volume, o passo 4 repõe os CSV demo da imagem.

---

## Docker local (já persistente)

`docker-compose.prod.yml` monta `./data:/data` — equivalente ao volume Railway:

```powershell
.\scripts\start_prod_docker.ps1
```

---

## Limitações actuais

| Dado | Persistência |
|------|----------------|
| CSV alunos + diário | Volume `/data` |
| Sessões chat | Supabase |
| RAG (pgvector) | Supabase |
| Chroma local | Não usado se `ROTINA_RAG_BACKEND=pgvector` |

**Próximo nível (futuro):** migrar cadastro/diário para **Postgres Supabase** em vez de CSV — elimina volume e Excel.

---

## Problemas comuns

### `/health` → `writable: false`

- Volume não montado ou mount path errado (tem de ser `/data`)
- Redeploy após criar volume

### CSV vazio / DuckDB falha

- Ver logs do arranque; confirmar `seedDir: "/app/seed-data"` no health
- Imagem deve incluir `COPY data /app/seed-data` (Dockerfile actual)

### Dados “voltaram ao demo” após deploy

- Volume não estava ligado ao serviço **api** correcto
- Dois serviços Railway — só **api** precisa do volume

---

Ver também: [PASSO_A_PASSO_PRODUCAO.md](PASSO_A_PASSO_PRODUCAO.md) · [FASE6_CUTOVER.md](FASE6_CUTOVER.md)
