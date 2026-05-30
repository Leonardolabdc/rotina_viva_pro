"""Configuração Supabase (Fase 1)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _normalize_supabase_url(url: str) -> str:
    u = url.rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[: -len("/rest/v1")]
    return u


def get_supabase_url() -> str:
    return _normalize_supabase_url(_env("SUPABASE_URL"))


def get_supabase_anon_key() -> str:
    return _env("SUPABASE_ANON_KEY")


def get_supabase_jwt_secret() -> str:
    return _env("SUPABASE_JWT_SECRET")


def get_supabase_demo_email_domain() -> str:
    return _env("SUPABASE_DEMO_EMAIL_DOMAIN") or "rotinaviva.local"


def __getattr__(name: str):
    if name == "SUPABASE_URL":
        return get_supabase_url()
    if name == "SUPABASE_ANON_KEY":
        return get_supabase_anon_key()
    if name == "SUPABASE_JWT_SECRET":
        return get_supabase_jwt_secret()
    if name == "SUPABASE_DEMO_EMAIL_DOMAIN":
        return get_supabase_demo_email_domain()
    raise AttributeError(name)


def supabase_configured() -> bool:
    return bool(get_supabase_url() and get_supabase_anon_key() and get_supabase_jwt_secret())


def supabase_env_status() -> dict[str, bool]:
    """Quais vars existem (sem expor valores) — útil em /health."""
    return {
        "SUPABASE_URL": bool(get_supabase_url()),
        "SUPABASE_ANON_KEY": bool(get_supabase_anon_key()),
        "SUPABASE_JWT_SECRET": bool(get_supabase_jwt_secret()),
    }
