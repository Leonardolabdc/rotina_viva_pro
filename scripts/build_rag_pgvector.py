#!/usr/bin/env python3
"""Indexa PDFs no Supabase pgvector (substitui Chroma local / build_rag_index.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from core.cloud_bootstrap import apply_cloud_bootstrap

apply_cloud_bootstrap()

from core.database import DATA_DIR
from modules.rag_index import INDEX_PROFILE, rag_backend
from modules.rag_pgvector import (
    ensure_pgvector_index,
    ingest_pgvector_documents,
    pgvector_configured,
    pgvector_needs_reingest,
)


def main() -> None:
    if not pgvector_configured():
        print("ERRO: defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env")
        sys.exit(1)
    print(f"DATA_DIR={DATA_DIR}")
    print(f"INDEX_PROFILE={INDEX_PROFILE}")
    print(f"ROTINA_RAG_BACKEND={rag_backend()}")
    if not pgvector_needs_reingest(DATA_DIR):
        n = ensure_pgvector_index(DATA_DIR)
        print(f"Índice pgvector já actualizado — {n} chunks no Supabase.")
        return
    print("A indexar PDFs no Supabase (embeddings via OpenRouter/OpenAI — consome tokens)...")
    n = ingest_pgvector_documents(DATA_DIR)
    print(f"Concluído — {n} chunks indexados em document_chunks (Supabase).")


if __name__ == "__main__":
    main()
