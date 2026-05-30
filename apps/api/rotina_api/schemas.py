"""Modelos alinhados ao contrato OpenAPI."""

from __future__ import annotations

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
