"""Rotas de autenticação — Supabase (Fase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from rotina_api.auth_service import SupabaseAuthError, login_with_password
from rotina_api.deps import get_current_user
from rotina_api.schemas import AuthSession, LoginRequest, UserProfile
from rotina_api.stubs import not_implemented
from rotina_api.supabase_settings import supabase_configured

router = APIRouter()


@router.post("/auth/login", operation_id="login", response_model=AuthSession)
async def login(body: LoginRequest) -> AuthSession:
    if not supabase_configured():
        raise not_implemented("login", phase="1")
    try:
        return login_with_password(body.username, body.password)
    except SupabaseAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": "unauthorized", "message": str(exc)},
        ) from exc


@router.post("/auth/logout", operation_id="logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_user: UserProfile = Depends(get_current_user)) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", operation_id="getCurrentUser", response_model=UserProfile)
async def get_current_user_route(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user
