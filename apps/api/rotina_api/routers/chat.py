"""Rotas de chat IA — reutiliza motor em `src/` (Fase 3)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from rotina_api.chat_store import ChatStoreError, create_session, fetch_student_name, get_session, save_session_messages
from rotina_api.deps import get_current_user
from rotina_api.schemas import (
    ChatMessage,
    ChatMessageResponse,
    ChatSession,
    CreateChatSessionRequest,
    GuardrailVerdict,
    RagChunk,
    SendChatMessageRequest,
    UserProfile,
)
from rotina_api.stubs import not_implemented
from rotina_api.supabase_settings import supabase_configured

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


def _token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail={"error": "unauthorized", "message": "Token em falta"})
    return credentials.credentials


def _require_worker() -> None:
    if not supabase_configured():
        raise not_implemented("chat", phase="1")


def _import_runner():
    from modules.api_chat_runner import (
        ApiUserContext,
        GuardrailBlockedError,
        QuotaExceededError,
        assistant_message,
        run_api_chat_turn,
        stream_api_chat_turn,
        user_message,
        verdict_to_api,
    )

    return (
        ApiUserContext,
        GuardrailBlockedError,
        QuotaExceededError,
        assistant_message,
        run_api_chat_turn,
        stream_api_chat_turn,
        user_message,
        verdict_to_api,
    )


async def _build_api_context(user: UserProfile, token: str):
    (
        ApiUserContext,
        *_,
    ) = _import_runner()
    student_name: str | None = None
    if user.role == "familia" and user.studentId is not None:
        try:
            student_name = fetch_student_name(token, user.studentId)
        except Exception:
            student_name = None
    return ApiUserContext(
        username=user.username,
        role=user.role,
        display_name=user.displayName,
        student_id=user.studentId,
        allow_mutations=user.allowMutations,
        student_name=student_name,
    )


def _history_for_model(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        if role in ("user", "assistant", "system") and content.strip():
            out.append({"role": role, "content": content})
    return out


def _handle_guardrail(exc: Exception) -> HTTPException:
    from modules.api_chat_runner import GuardrailBlockedError

    if isinstance(exc, GuardrailBlockedError):
        v = exc.verdict
        return HTTPException(
            status_code=422,
            detail={
                "allowed": False,
                "stage": v.stage or "input",
                "reason": v.user_message,
                "scanner": v.scanner,
                "riskScore": v.risk_score,
                "engine": v.engine,
                "audit": v.audit,
                "message": v.user_message,
            },
        )
    raise exc


def _handle_quota(exc: Exception) -> HTTPException:
    from modules.api_chat_runner import QuotaExceededError

    if isinstance(exc, QuotaExceededError):
        return HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": str(exc),
                "used": exc.used,
                "limit": exc.limit,
            },
        )
    raise exc


@router.post("/chat/sessions", operation_id="createChatSession", status_code=201, response_model=ChatSession)
async def create_chat_session(
    body: CreateChatSessionRequest | None = None,
    _user: UserProfile = Depends(get_current_user),
    token: str = Depends(_token_from_credentials),
) -> ChatSession:
    _require_worker()
    req = body or CreateChatSessionRequest()
    try:
        row = create_session(
            token,
            data_source_mode=req.dataSourceMode,
            crew_ai_enabled=req.crewAiEnabled,
            predictive_ml_enabled=req.predictiveMlEnabled,
        )
        return ChatSession(**row)
    except ChatStoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": "chat_store", "message": str(exc)}) from exc


@router.get("/chat/sessions/{session_id}", operation_id="getChatSession", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    _user: UserProfile = Depends(get_current_user),
    token: str = Depends(_token_from_credentials),
) -> ChatSession:
    _require_worker()
    try:
        row = get_session(token, session_id)
    except ChatStoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": "chat_store", "message": str(exc)}) from exc
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Sessão não encontrada"})
    return ChatSession(**row)


async def _process_message(
    session_id: str,
    body: SendChatMessageRequest,
    user: UserProfile,
    token: str,
) -> ChatMessageResponse:
    (
        _ApiUserContext,
        GuardrailBlockedError,
        QuotaExceededError,
        assistant_message,
        run_api_chat_turn,
        _stream,
        user_message,
        verdict_to_api,
    ) = _import_runner()

    session = get_session(token, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Sessão não encontrada"})

    mode = body.dataSourceMode or session.get("dataSourceMode") or "auto"
    crew = body.crewAiEnabled if body.crewAiEnabled is not None else bool(session.get("crewAiEnabled"))
    pred = (
        body.predictiveMlEnabled
        if body.predictiveMlEnabled is not None
        else bool(session.get("predictiveMlEnabled"))
    )

    messages: list[dict[str, Any]] = list(session.get("messages") or [])
    um = user_message(body.content)
    messages.append(um)
    history = _history_for_model(messages[:-1])

    try:
        ctx = await _build_api_context(user, token)
        result = run_api_chat_turn(
            ctx,
            content=body.content,
            history=history,
            data_source_mode=mode,
            crew_ai_enabled=crew,
            predictive_ml_enabled=pred,
            confirm_mutation=body.confirmMutation,
        )
    except GuardrailBlockedError as exc:
        raise _handle_guardrail(exc) from exc
    except QuotaExceededError as exc:
        raise _handle_quota(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": str(exc)}) from exc

    am = assistant_message(result.content)
    messages.append(am)
    try:
        save_session_messages(
            token,
            session_id,
            messages,
            data_source_mode=mode,
            crew_ai_enabled=crew,
            predictive_ml_enabled=pred,
        )
    except ChatStoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": "chat_store", "message": str(exc)}) from exc

    guardrail_payload = verdict_to_api(result.output_guardrail or result.input_guardrail)
    return ChatMessageResponse(
        message=ChatMessage(**am),
        ragChunks=[RagChunk(**c) for c in result.rag_chunks],
        guardrail=GuardrailVerdict(**guardrail_payload) if guardrail_payload else None,
        processingStatus=result.processing_status or None,
    )


@router.post("/chat/sessions/{session_id}/messages", operation_id="sendChatMessage", response_model=ChatMessageResponse)
async def send_chat_message(
    session_id: str,
    body: SendChatMessageRequest,
    user: UserProfile = Depends(get_current_user),
    token: str = Depends(_token_from_credentials),
) -> ChatMessageResponse:
    _require_worker()
    return await _process_message(session_id, body, user, token)


def _sse_line(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/sessions/{session_id}/messages/stream", operation_id="streamChatMessage")
async def stream_chat_message(
    session_id: str,
    body: SendChatMessageRequest,
    user: UserProfile = Depends(get_current_user),
    token: str = Depends(_token_from_credentials),
) -> StreamingResponse:
    _require_worker()

    (
        _ApiUserContext,
        GuardrailBlockedError,
        QuotaExceededError,
        assistant_message,
        _run,
        stream_api_chat_turn,
        user_message,
        _verdict_to_api,
    ) = _import_runner()

    session = get_session(token, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Sessão não encontrada"})

    mode = body.dataSourceMode or session.get("dataSourceMode") or "auto"
    crew = body.crewAiEnabled if body.crewAiEnabled is not None else bool(session.get("crewAiEnabled"))
    pred = (
        body.predictiveMlEnabled
        if body.predictiveMlEnabled is not None
        else bool(session.get("predictiveMlEnabled"))
    )

    messages: list[dict[str, Any]] = list(session.get("messages") or [])
    um = user_message(body.content)
    messages.append(um)
    history = _history_for_model(messages[:-1])

    try:
        ctx = await _build_api_context(user, token)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": str(exc)}) from exc

    def event_generator():
        try:
            final_content = ""
            rag_chunks: list[dict[str, Any]] = []
            processing_status = ""
            for ev in stream_api_chat_turn(
                ctx,
                content=body.content,
                history=history,
                data_source_mode=mode,
                crew_ai_enabled=crew,
                predictive_ml_enabled=pred,
                confirm_mutation=body.confirmMutation,
            ):
                name = str(ev.get("event") or "message")
                data = ev.get("data") or {}
                if name == "done":
                    final_content = str(data.get("content") or "")
                    rag_chunks = list(data.get("ragChunks") or [])
                    processing_status = str(data.get("processingStatus") or "")
                yield _sse_line(name, data if isinstance(data, dict) else {"value": data})

            am = assistant_message(final_content)
            messages.append(am)
            save_session_messages(
                token,
                session_id,
                messages,
                data_source_mode=mode,
                crew_ai_enabled=crew,
                predictive_ml_enabled=pred,
            )
        except GuardrailBlockedError as exc:
            yield _sse_line(
                "error",
                {
                    "code": 422,
                    "stage": "input",
                    "message": exc.verdict.user_message or "Mensagem bloqueada.",
                },
            )
        except QuotaExceededError as exc:
            yield _sse_line(
                "error",
                {"code": 429, "message": str(exc), "used": exc.used, "limit": exc.limit},
            )
        except Exception as exc:
            yield _sse_line("error", {"code": 500, "message": str(exc)})

    try:
        from core.database import DATA_DIR
        from core.guardrails import run_input_guardrails
        from core.security import check_llm_message_quota
        from modules.api_chat_runner import GuardrailBlockedError, QuotaExceededError

        recent = [
            str(m.get("content") or "")
            for m in history
            if m.get("role") == "user" and (m.get("content") or "").strip()
        ]
        verdict = run_input_guardrails(body.content, role=user.role, recent_user_messages=recent)
        if not verdict.allowed:
            raise GuardrailBlockedError(verdict)
        ok, used, limit = check_llm_message_quota(user.username, DATA_DIR)
        if not ok:
            raise QuotaExceededError(used, limit)
    except GuardrailBlockedError as exc:
        raise _handle_guardrail(exc) from exc
    except QuotaExceededError as exc:
        raise _handle_quota(exc) from exc

    return StreamingResponse(event_generator(), media_type="text/event-stream")
