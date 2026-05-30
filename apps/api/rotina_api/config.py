"""Configuração e dependências partilhadas da API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

OPENAPI_PATH = (
    _REPO_ROOT / "packages" / "api-contracts" / "openapi.yaml"
).resolve()

API_PHASE = os.getenv("ROTINA_API_PHASE", "0-monorepo")
API_VERSION = "0.1.0"
