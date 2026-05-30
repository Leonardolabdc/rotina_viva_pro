#!/usr/bin/env python3
"""Testa busca RAG no pgvector (linha de comando)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from modules.rag_pgvector import retrieve_rag_context_and_chunks_pg


def main() -> None:
    q = " ".join(sys.argv[1:]).strip() or "Qual o horário de funcionamento da escola?"
    block, chunks = retrieve_rag_context_and_chunks_pg(q)
    print(f"Pergunta: {q}\n")
    print("--- Contexto ---")
    print(block[:2000])
    print(f"\n--- {len(chunks)} chunk(s) na UI ---")
    for i, ch in enumerate(chunks, 1):
        print(f"{i}. {ch.get('source')} dist={ch.get('distance')}")


if __name__ == "__main__":
    main()
