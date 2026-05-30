"""Integração Supabase Auth + PostgREST."""

from __future__ import annotations

from typing import Any

import httpx
import jwt

from rotina_api.schemas import AuthSession, StudentSummary, UserProfile
from rotina_api.supabase_settings import (
    SUPABASE_ANON_KEY,
    SUPABASE_DEMO_EMAIL_DOMAIN,
    SUPABASE_JWT_SECRET,
    SUPABASE_URL,
)


class SupabaseAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


def resolve_login_email(username: str) -> str:
    raw = username.strip()
    if "@" in raw:
        return raw
    return f"{raw}@{SUPABASE_DEMO_EMAIL_DOMAIN}"


def _auth_user_from_token(token: str) -> dict[str, Any]:
    """Valida o token junto ao Supabase (funciona com JWT ES256/HS256)."""
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        if r.status_code >= 400:
            raise SupabaseAuthError("Token inválido ou expirado", status_code=401)
        data = r.json()
        if not isinstance(data, dict):
            raise SupabaseAuthError("Resposta inválida do Supabase Auth", status_code=502)
        return data


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Claims do utilizador autenticado.
    Projetos novos do Supabase usam ES256 — validamos via /auth/v1/user, não só JWT secret.
    """
    user = _auth_user_from_token(token)
    meta = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
    return {
        "sub": user.get("id"),
        "email": user.get("email"),
        "user_metadata": meta,
    }


def _decode_jwt_locally(token: str) -> dict[str, Any] | None:
    """Fallback legado HS256 (projectos antigos com JWT secret)."""
    if not SUPABASE_JWT_SECRET:
        return None
    try:
        return jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        return None


def login_with_password(username: str, password: str) -> AuthSession:
    email = resolve_login_email(username)
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        if r.status_code >= 400:
            try:
                payload = r.json()
            except Exception:
                payload = {}
            detail = (
                payload.get("msg")
                or payload.get("error_description")
                or payload.get("message")
                or "Credenciais inválidas"
            )
            raise SupabaseAuthError(str(detail), status_code=401)
        data = r.json()
        token = str(data["access_token"])
        profile = fetch_profile_with_token(token)
        return AuthSession(
            accessToken=token,
            expiresAt=str(data.get("expires_at")) if data.get("expires_at") else None,
            user=profile,
        )


def fetch_profile_with_token(token: str) -> UserProfile:
    user = _auth_user_from_token(token)
    user_id = str(user.get("id") or "")
    email = str(user.get("email") or "")
    meta = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}

    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            params={"id": f"eq.{user_id}", "select": "*"},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        r.raise_for_status()
        rows = r.json()
        if rows:
            row = rows[0]
            return UserProfile(
                username=email.split("@")[0] if email else user_id,
                role=str(row.get("role") or meta.get("role") or "familia"),
                displayName=str(row.get("display_name") or meta.get("display_name") or email),
                studentId=row.get("student_id"),
                allowMutations=bool(row.get("allow_mutations", False)),
            )

    return UserProfile(
        username=email.split("@")[0] if email else user_id,
        role=str(meta.get("role") or "familia"),
        displayName=str(meta.get("display_name") or email or user_id),
        studentId=int(meta["student_id"]) if meta.get("student_id") else None,
        allowMutations=bool(meta.get("allow_mutations", False)),
    )


def list_students_with_token(token: str, q: str | None = None) -> list[StudentSummary]:
    params: dict[str, str] = {"select": "id,name,class_name", "order": "name.asc"}
    if q and q.strip():
        params["name"] = f"ilike.*{q.strip()}*"

    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/students",
            params=params,
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        if r.status_code >= 400:
            raise SupabaseAuthError("Sem permissão para listar alunos", status_code=r.status_code)
        rows = r.json()
        return [
            StudentSummary(
                id=int(row["id"]),
                name=str(row["name"]),
                className=row.get("class_name"),
            )
            for row in rows
        ]
