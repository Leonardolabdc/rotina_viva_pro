"""
Arranque de `ROTINA_DATA_DIR` com volume persistente (Railway, Docker).

Copia CSVs demo de `ROTINA_SEED_DATA_DIR` só quando o volume está vazio —
nunca sobrescreve ficheiros já gravados (mutações do utilizador).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from core.cloud_bootstrap import ensure_rotina_users_file

# Ficheiros mínimos para DuckDB + demo local
_SEED_FILES = (
    "info_alunos.csv",
    "diario_estruturado.csv",
    "rotina_users.example.json",
    "chat_familia_educadores.json",
    "golden_dataset.json",
)

_SEED_DIRS = (
    "ml_models",
)


def _resolve_seed_dir(explicit: Path | None = None) -> Path | None:
    if explicit is not None and explicit.is_dir():
        return explicit.resolve()
    raw = (os.getenv("ROTINA_SEED_DATA_DIR") or "").strip()
    if raw:
        p = Path(raw).resolve()
        if p.is_dir():
            return p
    repo_data = Path(__file__).resolve().parents[2] / "data"
    if repo_data.is_dir():
        return repo_data.resolve()
    return None


def ensure_persistent_data_dir(
    data_dir: Path | None = None,
    seed_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Garante `ROTINA_DATA_DIR` pronto para DuckDB.

    Devolve metadados para `/health` (sem paths sensíveis extra).
    """
    data = (data_dir or Path(os.getenv("ROTINA_DATA_DIR", "data"))).resolve()
    seed = _resolve_seed_dir(seed_dir)
    data.mkdir(parents=True, exist_ok=True)

    info_csv = data / "info_alunos.csv"
    diario_csv = data / "diario_estruturado.csv"
    seeded_files: list[str] = []

    if not info_csv.is_file() and seed is not None:
        for name in _SEED_FILES:
            src = seed / name
            dst = data / name
            if src.is_file() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                    seeded_files.append(name)
                except OSError:
                    pass
        for dirname in _SEED_DIRS:
            src = seed / dirname
            dst = data / dirname
            if src.is_dir() and not dst.exists():
                try:
                    shutil.copytree(src, dst)
                    seeded_files.append(f"{dirname}/")
                except OSError:
                    pass

    ensure_rotina_users_file(data)

    writable = False
    probe = data / ".rotina_write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable = True
    except OSError:
        writable = False

    return {
        "path": str(data),
        "writable": writable,
        "infoAlunosCsv": info_csv.is_file(),
        "diarioCsv": diario_csv.is_file(),
        "seedDir": str(seed) if seed else None,
        "seededFiles": seeded_files,
        "persistentHint": (
            "Monte um volume Railway em /data para sobreviver a redeploys."
            if writable and info_csv.is_file()
            else "CSVs em falta — verifique volume ou ROTINA_SEED_DATA_DIR."
        ),
    }
