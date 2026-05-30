# Fase 4 — LLM Guard no worker

Integração da biblioteca [LLM Guard](https://github.com/protectai/llm-guard) (Protect AI) **em complemento** aos guardrails rule-based em `src/core/guardrails.py`.

> **Pré-requisito:** Fase 3 concluída (chat FastAPI operacional).

---

## O que muda

| Camada | Função |
|--------|--------|
| **Rule-based** (`guardrails.py`) | Regex, normalização, tópicos proibidos escolares — sempre activo |
| **LLM Guard** (`llm_guard_layer.py`) | ML: PromptInjection, Toxicity, InvisibleText (entrada); Toxicity, Sensitive (saída) |
| **API** | Campo `guardrail` nas respostas de chat com `engine`, `riskScore`, `audit` |

---

## Passo 1 — Instalar dependências

```powershell
cd d:\Dev\rotina_viva_pro\apps\api
pip install -r requirements-worker.txt
```

A 1.ª execução com LLM Guard activo pode **descarregar modelos** (vários minutos).

---

## Passo 2 — `.env`

```env
ROTINA_API_PHASE=4-llm-guard
ROTINA_LLM_GUARD_ENABLED=true
# ROTINA_LLM_GUARD_FAIL_OPEN=true   # default: continua só rule-based se ML falhar
# ROTINA_LLM_GUARD_INPUT_THRESHOLD=0.5
# ROTINA_LLM_GUARD_OUTPUT_THRESHOLD=0.5
```

Sem `ROTINA_LLM_GUARD_ENABLED=true`, a pipeline usa **apenas** rule-based (comportamento Fase 3).

---

## Passo 3 — Verificar `/health`

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Esperado com ML activo:

```json
{
  "phase": "4-llm-guard",
  "llmGuard": {
    "enabled": true,
    "available": true,
    "active": true,
    "inputScanners": ["InvisibleText", "PromptInjection", "Toxicity"],
    "outputScanners": ["Toxicity", "Sensitive"]
  }
}
```

---

## Passo 4 — Testes

```powershell
cd d:\Dev\rotina_viva_pro
.\scripts\test_guardrails.ps1
```

Inclui:
1. Health + estado LLM Guard
2. Mensagem legítima (passa)
3. Prompt injection (bloqueada — rule-based ou LLM Guard)

---

## Resposta da API (auditoria)

Exemplo em `POST /chat/sessions/{id}/messages`:

```json
{
  "message": { "role": "assistant", "content": "..." },
  "guardrail": {
    "allowed": true,
    "stage": "output",
    "engine": "hybrid",
    "riskScore": 0.12,
    "scanner": "ok",
    "audit": { "scores": { "Toxicity": 0.08 } }
  }
}
```

Bloqueio de entrada → HTTP **422** com o mesmo formato no `detail`.

---

## Arquitectura

```
Entrada do utilizador
  → run_input_guardrails (rule-based)
  → scan_input_llm_guard (ML, se activo)
  → motor src/ (plano, SQL, RAG, LLM)
  → run_output_guardrails (rule-based + scan_output_llm_guard)
  → resposta + guardrail audit
```

---

## Desactivar ML (dev leve)

```env
ROTINA_LLM_GUARD_ENABLED=false
```

Ou não instalar `llm-guard` — a API continua com rule-based.

---

## Próximo passo

**Fase 5** — frontend Next.js na Vercel consumindo este contrato HTTP.
