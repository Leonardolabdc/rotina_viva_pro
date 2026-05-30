"""Dependências FastAPI — JWT Supabase."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from rotina_api.auth_service import SupabaseAuthError, decode_access_token, fetch_profile_with_token
from rotina_api.schemas import UserProfile
from rotina_api.stubs import not_implemented
from rotina_api.supabase_settings import supabase_configured

_bearer = HTTPBearer(auto_error=False)


def require_supabase() -> None:
    if not supabase_configured():
        raise not_implemented("supabaseAuth", phase="1")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UserProfile:
    require_supabase()
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Token em falta"},
        )
    try:
        decode_access_token(credentials.credentials)
        return fetch_profile_with_token(credentials.credentials)
    except SupabaseAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": "unauthorized", "message": str(exc)},
        ) from exc
