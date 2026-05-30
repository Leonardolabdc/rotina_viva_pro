"""
Orquestração do chat para o worker FastAPI (sem Streamlit).

Reutiliza `rotina_inference` + guardrails/quota de `src/core`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generator

from core.auth_manager import (
    _chat_system_familia,
    _planner_suffix_familia,
    _planner_suffix_gestao,
    educador_rotina_csv_access,
)
from core.database import DATA_DIR
from typing import Any

from core.guardrails import (
    GuardrailVerdict,
    guardrail_verdict_to_dict,
    run_input_guardrails,
)
from core.security import check_llm_message_quota, record_llm_message
from modules.rotina_inference import (
    run_rotina_chat_turn,
    stream_rotina_chat_events,
)


class GuardrailBlockedError(Exception):
    def __init__(self, verdict: GuardrailVerdict) -> None:
        self.verdict = verdict
        super().__init__(verdict.user_message or "Mensagem bloqueada.")


class QuotaExceededError(Exception):
    def __init__(self, used: int, limit: int) -> None:
        self.used = used
        self.limit = limit
        super().__init__(f"Quota diária excedida ({used}/{limit}).")


@dataclass
class ApiChatTurnResult:
    content: str
    rag_chunks: list[dict[str, Any]]
    processing_status: str = ""
    input_guardrail: GuardrailVerdict | None = None
    output_guardrail: GuardrailVerdict | None = None


@dataclass
class ApiUserContext:
    username: str
    role: str
    display_name: str
    student_id: int | None
    allow_mutations: bool
    student_name: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _inference_kwargs(ctx: ApiUserContext, **overrides: Any) -> dict[str, Any]:
    role = (ctx.role or "").strip().lower()
    if role == "gestao":
        base = {
            "allow_mutations": ctx.allow_mutations,
            "allow_delete_mutations": True,
            "read_only_db": False,
            "planner_extra": _planner_suffix_gestao(),
            "chat_extra_system": None,
            "parent_scope": None,
        }
    elif role == "educador":
        acc = educador_rotina_csv_access()
        base = {
            "allow_mutations": bool(acc.get("allow_mutations")),
            "allow_delete_mutations": False,
            "read_only_db": bool(acc.get("read_only_db", False)),
            "planner_extra": acc.get("planner_extra"),
            "chat_extra_system": None,
            "parent_scope": None,
        }
    else:
        sid = ctx.student_id
        nome = (ctx.student_name or ctx.display_name or "aluno").strip()
        if sid is None:
            raise ValueError("Perfil família sem studentId vinculado.")
        base = {
            "allow_mutations": False,
            "allow_delete_mutations": False,
            "read_only_db": True,
            "planner_extra": _planner_suffix_familia(sid, nome),
            "chat_extra_system": _chat_system_familia(sid, nome),
            "parent_scope": (sid, nome),
        }
    base.update(overrides)
    base["audit_username"] = ctx.username
    base["audit_role"] = ctx.role
    return base


def _check_input_guardrails(
    content: str,
    history: list[dict[str, str]],
    role: str,
) -> GuardrailVerdict:
    recent = [
        str(m.get("content") or "")
        for m in history
        if m.get("role") == "user" and (m.get("content") or "").strip()
    ]
    verdict = run_input_guardrails(content, role=role, recent_user_messages=recent)
    if not verdict.allowed:
        raise GuardrailBlockedError(verdict)
    return verdict


def _check_and_record_quota(username: str) -> None:
    ok, used, limit = check_llm_message_quota(username, DATA_DIR)
    if not ok:
        raise QuotaExceededError(used, limit)
    record_llm_message(username, DATA_DIR)


def _rag_chunks_for_api(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in chunks:
        out.append(
            {
                "source": c.get("source") or c.get("metadata", {}).get("source"),
                "chunk": c.get("chunk") or c.get("text"),
                "distance": c.get("distance"),
                "text": c.get("text") or c.get("chunk"),
            }
        )
    return out


def run_api_chat_turn(
    ctx: ApiUserContext,
    *,
    content: str,
    history: list[dict[str, str]],
    data_source_mode: str = "auto",
    crew_ai_enabled: bool = False,
    predictive_ml_enabled: bool = False,
    confirm_mutation: bool = False,
) -> ApiChatTurnResult:
    text = (content or "").strip()
    input_guardrail = _check_input_guardrails(text, history, ctx.role)
    _check_and_record_quota(ctx.username)

    kwargs = _inference_kwargs(
        ctx,
        history=history,
        data_source_mode=data_source_mode,
        use_crewai=crew_ai_enabled,
        predictive_ml=predictive_ml_enabled,
        confirm_mutation=confirm_mutation,
    )
    result = run_rotina_chat_turn(text, **kwargs)
    return ApiChatTurnResult(
        content=result.content,
        rag_chunks=_rag_chunks_for_api(result.rag_chunks),
        processing_status=result.processing_status,
        input_guardrail=input_guardrail,
        output_guardrail=result.output_guardrail,
    )


def stream_api_chat_turn(
    ctx: ApiUserContext,
    *,
    content: str,
    history: list[dict[str, str]],
    data_source_mode: str = "auto",
    crew_ai_enabled: bool = False,
    predictive_ml_enabled: bool = False,
    confirm_mutation: bool = False,
) -> Generator[dict[str, Any], None, None]:
    text = (content or "").strip()
    _check_input_guardrails(text, history, ctx.role)
    _check_and_record_quota(ctx.username)

    kwargs = _inference_kwargs(
        ctx,
        history=history,
        data_source_mode=data_source_mode,
        use_crewai=crew_ai_enabled,
        predictive_ml=predictive_ml_enabled,
        confirm_mutation=confirm_mutation,
    )
    for event in stream_rotina_chat_events(text, **kwargs):
        if event.get("event") == "done":
            data = dict(event.get("data") or {})
            data["ragChunks"] = _rag_chunks_for_api(data.get("ragChunks") or [])
            event = {**event, "data": data}
        yield event


def assistant_message(content: str) -> dict[str, str]:
    return {"role": "assistant", "content": content, "createdAt": _utc_now_iso()}


def verdict_to_api(verdict: GuardrailVerdict | None) -> dict[str, Any] | None:
    if verdict is None:
        return None
    return guardrail_verdict_to_dict(verdict)


def user_message(content: str) -> dict[str, str]:
    return {"role": "user", "content": content, "createdAt": _utc_now_iso()}
