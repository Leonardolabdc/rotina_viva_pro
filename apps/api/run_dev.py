#!/usr/bin/env python3
"""Arranca uvicorn para desenvolvimento local."""

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


def _env_bool(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in ("1", "true", "yes", "on")


if __name__ == "__main__":
    # Reload duplo no Windows quebra import de torch/llm-guard no worker filho.
    use_reload = os.getenv("ROTINA_API_RELOAD", "").strip().lower()
    if use_reload in ("0", "false", "no", "off"):
        reload = False
    elif use_reload in ("1", "true", "yes", "on"):
        reload = True
    else:
        reload = not _env_bool("ROTINA_LLM_GUARD_ENABLED")

    uvicorn.run(
        "rotina_api.main:app",
        host="127.0.0.1",
        port=int(os.getenv("ROTINA_API_PORT", "8000")),
        reload=reload,
        reload_dirs=["rotina_api", "../../src"] if reload else None,
    )
