"""Importa info_alunos.csv e diario_estruturado.csv para Supabase (service role)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[: -len("/rest/v1")]
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DATA_DIR = Path(os.getenv("ROTINA_DATA_DIR", ROOT / "data"))


def _headers() -> dict[str, str]:
    if not SUPABASE_URL or not SERVICE_KEY:
        print("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env", file=sys.stderr)
        sys.exit(1)
    return {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def upsert_table(client: httpx.Client, table: str, rows: list[dict]) -> None:
    if not rows:
        print(f"  {table}: nada a importar")
        return
    batch = 500
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
            json=chunk,
        )
        r.raise_for_status()
    print(f"  {table}: {len(rows)} linhas")


def load_students() -> list[dict]:
    path = DATA_DIR / "info_alunos.csv"
    df = pd.read_csv(path)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "id": int(row["id_aluno"]),
                "name": str(row["nome"]),
                "class_name": str(row.get("turma") or ""),
                "allergies": str(row.get("alergias") or ""),
                "parent_contact": str(row.get("contato_pais") or ""),
            }
        )
    return rows


def load_diary() -> list[dict]:
    path = DATA_DIR / "diario_estruturado.csv"
    df = pd.read_csv(path)
    rows = []
    for _, row in df.iterrows():
        entry_date = row.get("data")
        if pd.notna(entry_date):
            entry_date = str(entry_date)[:10]
        else:
            entry_date = None
        rows.append(
            {
                "id": int(row["id_registro"]),
                "student_id": int(row["id_aluno"]),
                "entry_date": entry_date,
                "breakfast": _cell(row, "cafe_manha"),
                "lunch": _cell(row, "almoco"),
                "afternoon_snack": _cell(row, "lanche_tarde"),
                "extra_dinner": _cell(row, "jantar_extra"),
                "bathroom_changes": _int_or_none(row.get("trocas_banheiro")),
                "bowel_movement": _cell(row, "evacuacao"),
                "medications": _cell(row, "medicamentos"),
                "sleep_start": _cell(row, "hora_sono_inicio"),
                "sleep_end": _cell(row, "hora_sono_fim"),
                "sleep_quality": _cell(row, "qualidade_sono"),
                "day_activity": _cell(row, "atividade_dia"),
                "social_interaction": _cell(row, "interacao_social"),
                "teacher_note": _cell(row, "recado_professora"),
            }
        )
    return rows


def _cell(row: pd.Series, col: str) -> str | None:
    val = row.get(col)
    if pd.isna(val) or str(val).strip() == "":
        return None
    return str(val)


def _int_or_none(val: object) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def main() -> None:
    print("Importando CSVs para Supabase...")
    students = load_students()
    diary = load_diary()
    with httpx.Client(timeout=120.0) as client:
        upsert_table(client, "students", students)
        upsert_table(client, "diary_entries", diary)
    print("Concluído.")


if __name__ == "__main__":
    main()
