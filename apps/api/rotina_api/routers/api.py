"""Rotas HTTP — espelham packages/api-contracts/openapi.yaml (stubs Fase 3+)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, UploadFile

from rotina_api.deps import get_current_user
from rotina_api.schemas import UserProfile
from rotina_api.stubs import not_implemented

router = APIRouter()


@router.get("/reports/sleep-meal", operation_id="getSleepMealReport")
async def get_sleep_meal_report(
    studentName: str,
    studentId: int | None = None,
    _user: UserProfile = Depends(get_current_user),
) -> None:
    raise not_implemented("getSleepMealReport", phase="3")


@router.post("/transcribe", operation_id="transcribeAudio")
async def transcribe_audio(
    file: UploadFile,
    language: str = "pt",
    _user: UserProfile = Depends(get_current_user),
) -> None:
    raise not_implemented("transcribeAudio", phase="3")


@router.get("/direct-chat/students", operation_id="listDirectChatStudents")
async def list_direct_chat_students(
    _user: UserProfile = Depends(get_current_user),
) -> None:
    raise not_implemented("listDirectChatStudents", phase="3")


@router.get(
    "/direct-chat/students/{student_id}/messages",
    operation_id="listDirectChatMessages",
)
async def list_direct_chat_messages(
    student_id: int,
    _user: UserProfile = Depends(get_current_user),
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
    _user: UserProfile = Depends(get_current_user),
) -> None:
    raise not_implemented("sendDirectChatMessage", phase="3")
