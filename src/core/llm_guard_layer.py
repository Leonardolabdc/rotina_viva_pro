"""
Camada ML opcional (Protect AI llm-guard) — complementa guardrails rule-based.

Desligar: ROTINA_LLM_GUARD_ENABLED=false
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

_PROBE_CACHE: tuple[bool, str | None] | None = None


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or ("1" if default else "0")).strip().lower()
    return raw in ("1", "true", "yes", "on")


def llm_guard_enabled() -> bool:
    return _env_bool("ROTINA_LLM_GUARD_ENABLED", False)


def llm_guard_fail_open() -> bool:
    return _env_bool("ROTINA_LLM_GUARD_FAIL_OPEN", True)


def llm_guard_input_threshold() -> float:
    return float(os.getenv("ROTINA_LLM_GUARD_INPUT_THRESHOLD", "0.5"))


def llm_guard_output_threshold() -> float:
    return float(os.getenv("ROTINA_LLM_GUARD_OUTPUT_THRESHOLD", "0.5"))


def probe_llm_guard_import() -> tuple[bool, str | None]:
    """Testa import uma vez; guarda motivo se falhar (para /health)."""
    global _PROBE_CACHE
    if _PROBE_CACHE is not None:
        return _PROBE_CACHE
    try:
        import llm_guard  # noqa: F401

        _PROBE_CACHE = (True, None)
    except Exception as exc:
        _PROBE_CACHE = (False, f"{type(exc).__name__}: {exc}")
    return _PROBE_CACHE


def llm_guard_available() -> bool:
    ok, _ = probe_llm_guard_import()
    return ok


def warmup_llm_guard() -> dict[str, Any]:
    """
    Pré-carrega scanners (1.ª chamada lenta). Chamar no startup da API.
    """
    status = llm_guard_status()
    if not status.get("active"):
        return status
    try:
        from llm_guard.input_scanners import InvisibleText

        InvisibleText()
        status["warmedUp"] = True
    except Exception as exc:
        status["warmedUp"] = False
        status["warmupError"] = f"{type(exc).__name__}: {exc}"
    return status


def llm_guard_status() -> dict[str, Any]:
    enabled = llm_guard_enabled()
    available, import_error = probe_llm_guard_import()
    active = enabled and available
    scanners_in: list[str] = []
    scanners_out: list[str] = []
    if available:
        scanners_in = ["InvisibleText", "PromptInjection", "Toxicity"]
        scanners_out = ["Toxicity", "Sensitive"]
    out: dict[str, Any] = {
        "enabled": enabled,
        "available": available,
        "active": active,
        "failOpen": llm_guard_fail_open(),
        "inputScanners": scanners_in,
        "outputScanners": scanners_out,
        "python": sys.executable,
    }
    if import_error:
        out["importError"] = import_error
    return out


@dataclass(frozen=True)
class LLMGuardScanResult:
    allowed: bool
    scanner: str
    risk_score: float
    sanitized_text: str
    scores: dict[str, float] = field(default_factory=dict)


@lru_cache(maxsize=1)
def _input_scanners() -> list[Any]:
    from llm_guard.input_scanners import InvisibleText, PromptInjection, Toxicity

    threshold = llm_guard_input_threshold()
    return [
        InvisibleText(),
        PromptInjection(threshold=threshold),
        Toxicity(threshold=threshold),
    ]


@lru_cache(maxsize=1)
def _output_scanners() -> list[Any]:
    from llm_guard.output_scanners import Sensitive, Toxicity

    threshold = llm_guard_output_threshold()
    return [
        Toxicity(threshold=threshold),
        Sensitive(),
    ]


def _scores_from_results(results_score: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, val in (results_score or {}).items():
        try:
            out[str(key)] = float(val)
        except (TypeError, ValueError):
            continue
    return out


def scan_input_llm_guard(text: str) -> LLMGuardScanResult | None:
    if not llm_guard_enabled() or not llm_guard_available():
        return None
    payload = (text or "").strip()
    if not payload:
        return None
    try:
        from llm_guard import scan_prompt

        scanners = _input_scanners()
        sanitized, results_valid, results_score = scan_prompt(
            scanners, payload, fail_fast=True
        )
        scores = _scores_from_results(results_score)
        if any(not v for v in results_valid.values()):
            blocked = next(k for k, v in results_valid.items() if not v)
            return LLMGuardScanResult(
                allowed=False,
                scanner=f"llm_guard:{blocked}",
                risk_score=scores.get(str(blocked), 1.0),
                sanitized_text=sanitized,
                scores=scores,
            )
        max_score = max(scores.values()) if scores else 0.0
        return LLMGuardScanResult(
            allowed=True,
            scanner="llm_guard",
            risk_score=max_score,
            sanitized_text=sanitized,
            scores=scores,
        )
    except Exception:
        if llm_guard_fail_open():
            return None
        raise


def scan_output_llm_guard(prompt: str, response: str) -> LLMGuardScanResult | None:
    if not llm_guard_enabled() or not llm_guard_available():
        return None
    out = (response or "").strip()
    if not out:
        return None
    try:
        from llm_guard import scan_output

        scanners = _output_scanners()
        sanitized, results_valid, results_score = scan_output(
            scanners, (prompt or "").strip(), out, fail_fast=True
        )
        scores = _scores_from_results(results_score)
        if any(not v for v in results_valid.values()):
            blocked = next(k for k, v in results_valid.items() if not v)
            return LLMGuardScanResult(
                allowed=False,
                scanner=f"llm_guard:{blocked}",
                risk_score=scores.get(str(blocked), 1.0),
                sanitized_text=sanitized,
                scores=scores,
            )
        max_score = max(scores.values()) if scores else 0.0
        return LLMGuardScanResult(
            allowed=True,
            scanner="llm_guard",
            risk_score=max_score,
            sanitized_text=sanitized,
            scores=scores,
        )
    except Exception:
        if llm_guard_fail_open():
            return None
        raise
