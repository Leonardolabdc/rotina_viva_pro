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


SUPABASE_URL = _normalize_supabase_url(_env("SUPABASE_URL"))
SUPABASE_ANON_KEY = _env("SUPABASE_ANON_KEY")
SUPABASE_JWT_SECRET = _env("SUPABASE_JWT_SECRET")
SUPABASE_DEMO_EMAIL_DOMAIN = _env("SUPABASE_DEMO_EMAIL_DOMAIN") or "rotinaviva.local"


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_JWT_SECRET)
