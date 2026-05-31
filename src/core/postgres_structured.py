"""
Postgres (Supabase) como backend de cadastro + diário para o motor de chat.

Reutiliza views `info_alunos` / `diario_estruturado` (migration 20260531120000).
"""

from __future__ import annotations

import os
import re
from typing import Any

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from core.database import format_sql_rows


class _PgResult:
    def __init__(self, rows: list[Any], columns: list[str]) -> None:
        self._rows = rows
        self.description = [(c,) for c in columns]

    def fetchall(self) -> list[Any]:
        return self._rows

    def fetchone(self) -> Any | None:
        return self._rows[0] if self._rows else None


class PostgresStructuredConnection:
    """API mínima compatível com `duckdb` para `conn.execute(sql)`."""

    def execute(self, sql: str, params: list[Any] | None = None) -> _PgResult:
        pg_sql = _duckdb_sql_to_postgres(sql)
        with _pg_connect() as pg:
            with pg.cursor() as cur:
                cur.execute(pg_sql, params or [])
                if cur.description is None:
                    return _PgResult([], [])
                cols = [d.name for d in cur.description]
                rows = cur.fetchall()
        return _PgResult(list(rows), cols)


def structured_data_backend() -> str:
    raw = (os.getenv("ROTINA_DATA_BACKEND") or "csv").strip().lower()
    if raw in ("supabase", "postgres", "pg"):
        return "supabase"
    return "csv"


def postgres_database_url() -> str:
    for key in ("DATABASE_URL", "SUPABASE_DB_URL", "SUPABASE_DATABASE_URL"):
        val = (os.getenv(key) or "").strip()
        if val:
            return val
    return ""


# Parâmetros de query na URI Supabase/Prisma que psycopg não aceita (ex.: ?pgbouncer=true).
_PSQL_URI_DROP_QUERY_PARAMS = frozenset({"pgbouncer", "connection_limit", "pool_timeout"})


def psycopg_connect_url(raw_url: str) -> str:
    """URI Postgres compatível com psycopg (remove ?pgbouncer=true, etc.)."""
    s = (raw_url or "").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    s = re.sub(r"[?&]pgbouncer=[^&]*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\?&", "?", s)
    s = re.sub(r"\?$", "", s)

    parsed = urlparse(s)
    if not parsed.query:
        return s
    kept = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _PSQL_URI_DROP_QUERY_PARAMS
    ]
    return urlunparse(parsed._replace(query=urlencode(kept) if kept else ""))


def postgres_configured() -> bool:
    return bool(postgres_database_url())


def supabase_structured_ready() -> bool:
    return structured_data_backend() == "supabase" and postgres_configured()


def _probe_error_hint(exc: Exception) -> str | None:
    msg = str(exc).lower()
    if "pgbouncer" in msg and "query parameter" in msg:
        return "Remova ?pgbouncer=true do DATABASE_URL no Railway."
    if "prepared statement" in msg and "already exists" in msg:
        return (
            "Pooler transaction (porta 6543): use Session pooler na porta 5432 no DATABASE_URL "
            "(Supabase → Connect → Session mode), ou aguarde redeploy recente do worker."
        )
    return None


def supabase_structured_probe() -> dict[str, object]:
    """Testa SELECT na view info_alunos (health / diagnóstico)."""
    if not supabase_structured_ready():
        return {"ok": False, "reason": "not_configured"}
    raw = postgres_database_url()
    try:
        with _pg_connect() as pg:
            with pg.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS total FROM info_alunos "
                    "WHERE TRIM(COALESCE(nome, '')) <> ''"
                )
                row = cur.fetchone()
        total = int(row[0]) if row else 0
        out: dict[str, object] = {"ok": True, "studentsWithName": total}
        if "pgbouncer" in raw.lower():
            out["note"] = "DATABASE_URL continha pgbouncer=; removido automaticamente para psycopg."
        return out
    except Exception as exc:
        return {"ok": False, "error": str(exc), "hint": _probe_error_hint(exc)}


def _pg_connect() -> Any:
    """Nova ligação por consulta — compatível com Supavisor transaction mode (6543)."""
    import psycopg

    url = postgres_database_url()
    if not url:
        raise RuntimeError(
            "ROTINA_DATA_BACKEND=supabase requer DATABASE_URL (ou SUPABASE_DB_URL) "
            "— Supabase → Settings → Database → Connection string."
        )
    connect_url = psycopg_connect_url(url)
    return psycopg.connect(connect_url, autocommit=True, prepare_threshold=None)


def reset_postgres_connection() -> None:
    """Compatibilidade — ligações Postgres são efémeras (sem pool global)."""
    return None


def open_postgres_structured_connection() -> PostgresStructuredConnection:
    return PostgresStructuredConnection()


def run_safe_select_postgres(sql: str) -> tuple[str, bool]:
    from core.database import validate_sql

    if not validate_sql(sql):
        return "Consulta SQL rejeitada (apenas SELECT nas tabelas permitidas).", False
    try:
        conn = open_postgres_structured_connection()
        cur = conn.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return format_sql_rows(rows, cols), True
    except Exception as e:
        hint = _probe_error_hint(e)
        msg = f"Erro ao executar SQL: {e}"
        if hint:
            msg += f" ({hint})"
        return msg, False


def _duckdb_sql_to_postgres(sql: str) -> str:
    """Ajustes pontuais DuckDB → Postgres (mesmas tabelas/colunas via views)."""
    s = sql.strip().rstrip(";")
    return re.sub(
        r"\bCURRENT_DATE\b",
        "CURRENT_DATE",
        s,
        flags=re.IGNORECASE,
    )
