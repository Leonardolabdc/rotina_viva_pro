"""Ponto de entrada FastAPI — Rotina Viva Pro."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from rotina_api.config import API_PHASE, API_VERSION, OPENAPI_PATH
from rotina_api.routers import api, auth, chat, students
from rotina_api.supabase_settings import supabase_configured, supabase_env_status

_LLM_GUARD_BOOT: dict[str, object] = {}
_DATA_DIR_BOOT: dict[str, object] = {}


def _worker_ready() -> bool:
    try:
        import duckdb  # noqa: F401
        from modules import rotina_inference  # noqa: F401

        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _LLM_GUARD_BOOT, _DATA_DIR_BOOT
    try:
        from core.data_bootstrap import ensure_persistent_data_dir

        _DATA_DIR_BOOT = ensure_persistent_data_dir()
    except Exception as exc:
        _DATA_DIR_BOOT = {"error": str(exc)}
    if _worker_ready():
        try:
            from core.llm_guard_layer import warmup_llm_guard

            _LLM_GUARD_BOOT = warmup_llm_guard()
        except Exception as exc:
            _LLM_GUARD_BOOT = {"warmupError": str(exc)}
    yield


app = FastAPI(
    title="Rotina Viva API",
    version=API_VERSION,
    description="Worker HTTP — reutiliza lógica em `src/` (Fase 3+).",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    import os

    raw = os.getenv(
        "ROTINA_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"], operation_id="getHealth")
async def health() -> dict[str, object]:
    import os

    phase = os.getenv("ROTINA_API_PHASE", API_PHASE).strip() or API_PHASE
    if supabase_configured() and phase.startswith("0"):
        phase = "1-supabase"
    if phase in ("1-supabase", "3-fastapi-worker") and _worker_ready():
        phase = "3-fastapi-worker"
    llm_guard: dict[str, object] = dict(_LLM_GUARD_BOOT) if _LLM_GUARD_BOOT else {
        "enabled": False,
        "available": False,
        "active": False,
    }
    if _worker_ready() and not llm_guard:
        try:
            from core.llm_guard_layer import llm_guard_status

            llm_guard = llm_guard_status()
        except Exception as exc:
            llm_guard = {"enabled": False, "available": False, "active": False, "error": str(exc)}
    if llm_guard.get("active"):
        phase = "4-llm-guard"
    structured: dict[str, object] = {}
    try:
        from core.postgres_structured import (
            postgres_configured,
            structured_data_backend,
            supabase_structured_probe,
            supabase_structured_ready,
        )

        structured = {
            "backend": structured_data_backend(),
            "postgresConfigured": postgres_configured(),
            "ready": supabase_structured_ready(),
        }
        if supabase_structured_ready():
            structured["probe"] = supabase_structured_probe()
    except Exception as exc:
        structured = {"error": str(exc)}
    return {
        "status": "ok",
        "version": API_VERSION,
        "phase": phase,
        "supabase": "configured" if supabase_configured() else "missing",
        "supabaseEnv": supabase_env_status(),
        "dataDir": _DATA_DIR_BOOT or None,
        "structuredData": structured,
        "llmGuard": llm_guard,
    }


@app.get("/openapi.yaml", include_in_schema=False)
async def serve_contract_yaml() -> PlainTextResponse:
    if not OPENAPI_PATH.is_file():
        return PlainTextResponse("openapi.yaml not found", status_code=404)
    return PlainTextResponse(
        OPENAPI_PATH.read_text(encoding="utf-8"),
        media_type="application/yaml",
    )


@app.get("/openapi.json", include_in_schema=False)
async def serve_contract_json() -> JSONResponse:
    if not OPENAPI_PATH.is_file():
        return JSONResponse({"error": "openapi.yaml not found"}, status_code=404)
    data = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    return JSONResponse(data)


app.include_router(auth.router)
app.include_router(students.router)
app.include_router(chat.router)
app.include_router(api.router)
