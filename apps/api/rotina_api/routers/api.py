"""Rotas HTTP — espelham packages/api-contracts/openapi.yaml."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, UploadFile

from rotina_api.stubs import not_implemented

router = APIRouter()


def _require_auth() -> dict[str, Any]:
    """Placeholder — Fase 1 valida JWT Supabase."""
    raise not_implemented("requireAuth", phase="1")


@router.post("/auth/login", operation_id="login")
async def login(_body: dict[str, Any]) -> None:
    raise not_implemented("login", phase="1")


@router.post("/auth/logout", operation_id="logout")
async def logout(_user: dict[str, Any] = Depends(_require_auth)) -> None:
    raise not_implemented("logout", phase="1")


@router.get("/auth/me", operation_id="getCurrentUser")
async def get_current_user(_user: dict[str, Any] = Depends(_require_auth)) -> None:
    raise not_implemented("getCurrentUser", phase="1")


@router.post("/chat/sessions", operation_id="createChatSession", status_code=201)
async def create_chat_session(
    _body: dict[str, Any] | None = None,
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("createChatSession", phase="3")


@router.get("/chat/sessions/{session_id}", operation_id="getChatSession")
async def get_chat_session(
    session_id: str,
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("getChatSession", phase="3")


@router.post("/chat/sessions/{session_id}/messages", operation_id="sendChatMessage")
async def send_chat_message(
    session_id: str,
    _body: dict[str, Any],
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("sendChatMessage", phase="3")


@router.post(
    "/chat/sessions/{session_id}/messages/stream",
    operation_id="streamChatMessage",
)
async def stream_chat_message(
    session_id: str,
    _body: dict[str, Any],
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("streamChatMessage", phase="3")


@router.get("/reports/sleep-meal", operation_id="getSleepMealReport")
async def get_sleep_meal_report(
    studentName: str,
    studentId: int | None = None,
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("getSleepMealReport", phase="3")


@router.post("/transcribe", operation_id="transcribeAudio")
async def transcribe_audio(
    file: UploadFile,
    language: str = "pt",
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("transcribeAudio", phase="3")


@router.get("/direct-chat/students", operation_id="listDirectChatStudents")
async def list_direct_chat_students(
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("listDirectChatStudents", phase="3")


@router.get(
    "/direct-chat/students/{student_id}/messages",
    operation_id="listDirectChatMessages",
)
async def list_direct_chat_messages(
    student_id: int,
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("listDirectChatMessages", phase="3")


@router.post(
    "/direct-chat/students/{student_id}/messages",
    operation_id="sendDirectChatMessage",
    status_code=201,
)
async def send_direct_chat_message(
    student_id: int,
    _body: dict[str, Any],
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("sendDirectChatMessage", phase="3")


@router.get("/students", operation_id="listStudents")
async def list_students(
    q: str | None = None,
    _user: dict[str, Any] = Depends(_require_auth),
) -> None:
    raise not_implemented("listStudents", phase="1")
