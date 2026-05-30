"""Rotas de alunos — escopo RBAC via Supabase RLS (Fase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from rotina_api.auth_service import SupabaseAuthError, list_students_with_token
from rotina_api.deps import get_current_user
from rotina_api.schemas import StudentSummary, UserProfile
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


@router.get("/students", operation_id="listStudents", response_model=list[StudentSummary])
async def list_students(
    q: str | None = None,
    _user: UserProfile = Depends(get_current_user),
    token: str = Depends(_token_from_credentials),
) -> list[StudentSummary]:
    if not supabase_configured():
        raise not_implemented("listStudents", phase="1")
    try:
        return list_students_with_token(token, q=q)
    except SupabaseAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": "forbidden", "message": str(exc)},
        ) from exc
