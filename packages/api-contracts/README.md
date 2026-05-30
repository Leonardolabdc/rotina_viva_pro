# @rotina-viva/api-contracts

Contrato **OpenAPI 3.1** entre o frontend (`apps/web`) e o worker (`apps/api`).

## Ficheiros

| Ficheiro | Função |
|----------|--------|
| `openapi.yaml` | Fonte da verdade — rotas, schemas, RBAC |
| `generated/schema.d.ts` | Tipos TypeScript gerados (não editar à mão) |

## Comandos

```bash
pnpm --filter @rotina-viva/api-contracts validate
pnpm --filter @rotina-viva/api-contracts generate
```

## Evolução por fase

| Fase | Alterações previstas no contrato |
|------|----------------------------------|
| **0** | Rotas documentadas; stubs 501 na API |
| **1** | Auth → JWT Supabase; CRUD alunos/diário via Postgres |
| **2** | Endpoints de ingestão RAG / busca pgvector |
| **3** | Implementação real em FastAPI (reutiliza `src/`) |
| **4** | Campos de auditoria LLM Guard nos responses |
