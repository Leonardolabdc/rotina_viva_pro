"""Cria utilizadores demo no Supabase Auth + metadata para profiles (trigger)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[: -len("/rest/v1")]
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

DEMO_USERS: tuple[dict, ...] = (
    {
        "email": "gestao.demo@rotinaviva.local",
        "password": "demo123",
        "role": "gestao",
        "display_name": "Gestão (edição)",
        "allow_mutations": True,
    },
    {
        "email": "professor.demo@rotinaviva.local",
        "password": "demo123",
        "role": "educador",
        "display_name": "Prof. Demonstração",
        "allow_mutations": False,
    },
    {
        "email": "pai.demo@rotinaviva.local",
        "password": "demo123",
        "role": "familia",
        "display_name": "Responsável (Rafael Souza)",
        "student_id": 1,
        "allow_mutations": False,
    },
)


def _admin_headers() -> dict[str, str]:
    if not SUPABASE_URL or not SERVICE_KEY:
        print("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env", file=sys.stderr)
        sys.exit(1)
    return {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }


def create_user(client: httpx.Client, spec: dict) -> None:
    meta: dict = {
        "role": spec["role"],
        "display_name": spec["display_name"],
        "allow_mutations": spec.get("allow_mutations", False),
    }
    if spec.get("student_id") is not None:
        meta["student_id"] = str(spec["student_id"])

    body = {
        "email": spec["email"],
        "password": spec["password"],
        "email_confirm": True,
        "user_metadata": meta,
    }
    r = client.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=_admin_headers(),
        json=body,
    )
    if r.status_code == 422 and "already been registered" in r.text:
        print(f"  {spec['email']}: já existe (ignorado)")
        return
    r.raise_for_status()
    print(f"  {spec['email']}: criado ({spec['role']})")


def main() -> None:
    print("Criando utilizadores demo no Supabase Auth...")
    with httpx.Client(timeout=60.0) as client:
        for spec in DEMO_USERS:
            create_user(client, spec)
    print("Concluído. Teste login na API com o email (não o username antigo).")


if __name__ == "__main__":
    main()
