"""Ponto de entrada FastAPI — Rotina Viva Pro."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from rotina_api.config import API_PHASE, API_VERSION, OPENAPI_PATH
from rotina_api.routers import api

app = FastAPI(
    title="Rotina Viva API",
    version=API_VERSION,
    description="Worker HTTP — reutiliza lógica em `src/` (Fase 3+).",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"], operation_id="getHealth")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": API_VERSION,
        "phase": API_PHASE,
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


app.include_router(api.router)
