#!/usr/bin/env python3
"""Arranca uvicorn para produção (Docker / Railway / Fly)."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

_REPO_ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass

if __name__ == "__main__":
    # LLM Guard + torch: um único worker; reload desligado.
    uvicorn.run(
        "rotina_api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", os.getenv("ROTINA_API_PORT", "8000"))),
        workers=1,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
