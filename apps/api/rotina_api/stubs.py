"""Respostas padronizadas para rotas ainda não implementadas (Fase 3)."""

from __future__ import annotations

from fastapi import HTTPException, status


def not_implemented(operation_id: str, phase: str = "3") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "not_implemented",
            "message": (
                f"Operação `{operation_id}` documentada no contrato OpenAPI; "
                f"implementação prevista na Fase {phase}."
            ),
            "operationId": operation_id,
        },
    )
