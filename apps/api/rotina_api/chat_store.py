"""Persistência de sessões de chat no Supabase (tabela chat_sessions)."""

from __future__ import annotations

from typing import Any

import httpx

from rotina_api.auth_service import SupabaseAuthError, decode_access_token
from rotina_api.supabase_settings import SUPABASE_ANON_KEY, SUPABASE_URL


class ChatStoreError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _headers(token: str) -> dict[str, str]:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _row_to_session(row: dict[str, Any]) -> dict[str, Any]:
    messages = row.get("messages") or []
    if not isinstance(messages, list):
        messages = []
    return {
        "id": str(row["id"]),
        "messages": messages,
        "dataSourceMode": row.get("data_source_mode") or "auto",
        "crewAiEnabled": bool(row.get("crew_ai_enabled", False)),
        "predictiveMlEnabled": bool(row.get("predictive_ml_enabled", False)),
    }


def create_session(
    token: str,
    *,
    data_source_mode: str = "auto",
    crew_ai_enabled: bool = False,
    predictive_ml_enabled: bool = False,
) -> dict[str, Any]:
    payload = {
        "user_id": user_id_from_token(token),
        "data_source_mode": data_source_mode,
        "crew_ai_enabled": crew_ai_enabled,
        "predictive_ml_enabled": predictive_ml_enabled,
        "messages": [],
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/chat_sessions",
            headers=_headers(token),
            json=payload,
        )
        if r.status_code >= 400:
            raise ChatStoreError(f"Não foi possível criar sessão: {r.text}", status_code=r.status_code)
        rows = r.json()
        if not rows:
            raise ChatStoreError("Sessão não devolvida pelo Supabase", status_code=502)
        return _row_to_session(rows[0])


def get_session(token: str, session_id: str) -> dict[str, Any] | None:
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/chat_sessions",
            params={"id": f"eq.{session_id}", "select": "*"},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        if r.status_code >= 400:
            raise ChatStoreError(f"Erro ao obter sessão: {r.text}", status_code=r.status_code)
        rows = r.json()
        if not rows:
            return None
        return _row_to_session(rows[0])


def save_session_messages(
    token: str,
    session_id: str,
    messages: list[dict[str, Any]],
    *,
    data_source_mode: str | None = None,
    crew_ai_enabled: bool | None = None,
    predictive_ml_enabled: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"messages": messages}
    if data_source_mode is not None:
        payload["data_source_mode"] = data_source_mode
    if crew_ai_enabled is not None:
        payload["crew_ai_enabled"] = crew_ai_enabled
    if predictive_ml_enabled is not None:
        payload["predictive_ml_enabled"] = predictive_ml_enabled

    with httpx.Client(timeout=30.0) as client:
        r = client.patch(
            f"{SUPABASE_URL}/rest/v1/chat_sessions",
            params={"id": f"eq.{session_id}"},
            headers=_headers(token),
            json=payload,
        )
        if r.status_code >= 400:
            raise ChatStoreError(f"Erro ao gravar mensagens: {r.text}", status_code=r.status_code)
        rows = r.json()
        if not rows:
            updated = get_session(token, session_id)
            if updated is None:
                raise ChatStoreError("Sessão não encontrada após update", status_code=404)
            return updated
        return _row_to_session(rows[0])


def fetch_student_name(token: str, student_id: int) -> str | None:
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/students",
            params={"id": f"eq.{student_id}", "select": "name"},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        if r.status_code >= 400:
            raise SupabaseAuthError("Sem permissão para ler aluno", status_code=r.status_code)
        rows = r.json()
        if not rows:
            return None
        return str(rows[0].get("name") or "")


def user_id_from_token(token: str) -> str:
    claims = decode_access_token(token)
    uid = claims.get("sub")
    if not uid:
        raise SupabaseAuthError("Token sem identificador de utilizador", status_code=401)
    return str(uid)
