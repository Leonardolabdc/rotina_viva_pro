"""
Postgres (Supabase) como backend de cadastro + diário para o motor de chat.

Reutiliza views `info_alunos` / `diario_estruturado` (migration 20260531120000).
"""

from __future__ import annotations

import os
import re
from typing import Any

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

    def __init__(self) -> None:
        self._conn = _get_pg_connection()

    def execute(self, sql: str, params: list[Any] | None = None) -> _PgResult:
        import psycopg

        pg_sql = _duckdb_sql_to_postgres(sql)
        with self._conn.cursor() as cur:
            cur.execute(pg_sql, params or [])
            if cur.description is None:
                return _PgResult([], [])
            cols = [d.name for d in cur.description]
            rows = cur.fetchall()
        return _PgResult(list(rows), cols)


_pg_conn: Any | None = None


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


def postgres_configured() -> bool:
    return bool(postgres_database_url())


def supabase_structured_ready() -> bool:
    return structured_data_backend() == "supabase" and postgres_configured()


def _get_pg_connection() -> Any:
    global _pg_conn
    url = postgres_database_url()
    if not url:
        raise RuntimeError(
            "ROTINA_DATA_BACKEND=supabase requer DATABASE_URL (ou SUPABASE_DB_URL) "
            "— Supabase → Settings → Database → Connection string."
        )
    import psycopg

    if _pg_conn is None or getattr(_pg_conn, "closed", False):
        _pg_conn = psycopg.connect(url, autocommit=True)
    return _pg_conn


def reset_postgres_connection() -> None:
    global _pg_conn
    if _pg_conn is not None:
        try:
            _pg_conn.close()
        except Exception:
            pass
    _pg_conn = None


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
        return f"Erro ao executar SQL: {e}", False


def _duckdb_sql_to_postgres(sql: str) -> str:
    """Ajustes pontuais DuckDB → Postgres (mesmas tabelas/colunas via views)."""
    s = sql.strip().rstrip(";")
    # DuckDB aceita comparar date column com string; views já expõem text onde necessário.
    return re.sub(
        r"\bCURRENT_DATE\b",
        "CURRENT_DATE",
        s,
        flags=re.IGNORECASE,
    )
