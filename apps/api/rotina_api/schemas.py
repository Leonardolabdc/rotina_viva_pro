"""Modelos alinhados ao contrato OpenAPI."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, description="Email ou username demo (ex.: gestao.demo)")
    password: str = Field(min_length=1)


class UserProfile(BaseModel):
    username: str
    role: str
    displayName: str
    studentId: int | None = None
    allowMutations: bool = False


class AuthSession(BaseModel):
    accessToken: str
    expiresAt: str | None = None
    user: UserProfile


class StudentSummary(BaseModel):
    id: int
    name: str
    className: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str
    createdAt: str | None = None


class ChatSession(BaseModel):
    id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    dataSourceMode: str = "auto"
    crewAiEnabled: bool = False
    predictiveMlEnabled: bool = False


class CreateChatSessionRequest(BaseModel):
    dataSourceMode: str = "auto"
    crewAiEnabled: bool = False
    predictiveMlEnabled: bool = False


class SendChatMessageRequest(BaseModel):
    content: str = Field(min_length=1)
    dataSourceMode: str | None = None
    crewAiEnabled: bool | None = None
    predictiveMlEnabled: bool | None = None
    confirmMutation: bool = False


class RagChunk(BaseModel):
    source: str | None = None
    chunk: str | None = None
    distance: float | None = None
    text: str | None = None


class GuardrailVerdict(BaseModel):
    allowed: bool
    stage: str
    reason: str | None = None
    scanner: str | None = None
    redactedContent: str | None = None
    riskScore: float | None = None
    engine: str | None = None
    audit: dict[str, Any] | None = None


class ChatMessageResponse(BaseModel):
    message: ChatMessage
    ragChunks: list[RagChunk] = Field(default_factory=list)
    guardrail: GuardrailVerdict | None = None
    processingStatus: str | None = None
