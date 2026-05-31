"""RAG com pgvector no Supabase (Fase 2) — substitui ChromaDB local."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

from modules.chat_service import (
    is_rag_identity_scope_question,
    is_rag_nutrition_meals_scope_question,
)
from modules.rag_index import (
    INDEX_PROFILE,
    MAX_CHUNKS_PER_PDF,
    MAX_CHUNKS_TOTAL,
    PDF_NAMES,
    PPP_PEDAGOGICO_PDF,
    PPP_SKIP_FIRST_PAGES,
    RAG_IDENTITY_SOURCES,
    RAG_NUTRITION_SOURCES,
    RAG_TOP_K,
    ROTINA_API_PAUSE_BETWEEN_PDF_SEC,
    ROTINA_RAG_DISTANCE_GAP,
    ROTINA_RAG_LEXICAL_WEIGHT,
    _rag_pdf_manifest_fingerprint,
    _rag_text_for_embedding_index,
    build_chroma_embedding_function,
    chunk_pdf_for_index,
    effective_chroma_add_batch,
    extract_pdf_text,
    select_rag_chunks_from_candidates,
)

_EMBED_DIM = int(os.getenv("OPENAI_EMBED_DIMENSIONS", "1536") or "1536")
_META_FINGERPRINT_KEY = "pdf_manifest_fingerprint"
_META_PROFILE_KEY = "index_profile"
_META_CHUNK_COUNT_KEY = "chunk_count"


def _normalize_url(url: str) -> str:
    u = url.rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[: -len("/rest/v1")]
    return u


SUPABASE_URL = _normalize_url(os.getenv("SUPABASE_URL", ""))
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def pgvector_configured() -> bool:
    return bool(SUPABASE_URL and SERVICE_KEY)


def pgvector_chunk_count() -> int:
    """Chunks indexados no Supabase (0 se não configurado ou erro)."""
    if not pgvector_configured():
        return 0
    try:
        with httpx.Client(timeout=15.0) as client:
            return _count_chunks(client, INDEX_PROFILE)
    except Exception:
        return 0


def pgvector_rag_health() -> dict[str, object]:
    backend = os.getenv("ROTINA_RAG_BACKEND", "chroma").strip().lower()
    if backend != "pgvector":
        return {"backend": backend or "chroma"}
    if not pgvector_configured():
        return {"backend": "pgvector", "configured": False, "ready": False}
    try:
        n = pgvector_chunk_count()
        return {
            "backend": "pgvector",
            "configured": True,
            "chunkCount": n,
            "ready": n > 0,
        }
    except Exception as exc:
        return {
            "backend": "pgvector",
            "configured": True,
            "ready": False,
            "error": str(exc),
        }


def _service_headers() -> dict[str, str]:
    return {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }


def _auth_headers(token: str | None = None) -> dict[str, str]:
    key = token or ANON_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    ef = build_chroma_embedding_function()
    if hasattr(ef, "embed_query"):
        vecs = ef.embed_query(texts)
    else:
        vecs = ef(texts)
    out: list[list[float]] = []
    for v in vecs:
        if hasattr(v, "tolist"):
            out.append([float(x) for x in v.tolist()])
        else:
            out.append([float(x) for x in v])
    return out


def _get_meta(client: httpx.Client, key: str) -> str | None:
    r = client.get(
        f"{SUPABASE_URL}/rest/v1/rag_index_meta",
        params={"key": f"eq.{key}", "select": "value"},
        headers=_service_headers(),
    )
    if r.status_code >= 400:
        return None
    rows = r.json()
    if rows and isinstance(rows, list):
        return str(rows[0].get("value") or "") or None
    return None


def _set_meta(client: httpx.Client, key: str, value: str) -> None:
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/rag_index_meta",
        headers={**_service_headers(), "Prefer": "resolution=merge-duplicates"},
        json={"key": key, "value": value},
    )
    r.raise_for_status()


def _count_chunks(client: httpx.Client, profile: str) -> int:
    r = client.get(
        f"{SUPABASE_URL}/rest/v1/document_chunks",
        params={"index_profile": f"eq.{profile}", "select": "id"},
        headers={**_service_headers(), "Prefer": "count=exact"},
    )
    r.raise_for_status()
    cr = r.headers.get("content-range", "")
    if "/" in cr:
        try:
            return int(cr.split("/")[-1])
        except ValueError:
            pass
    rows = r.json()
    return len(rows) if isinstance(rows, list) else 0


def _delete_profile_chunks(client: httpx.Client, profile: str) -> None:
    r = client.delete(
        f"{SUPABASE_URL}/rest/v1/document_chunks",
        params={"index_profile": f"eq.{profile}"},
        headers=_service_headers(),
    )
    r.raise_for_status()


def _pdfs_available_in(data_dir: Path) -> bool:
    return any((data_dir / name).is_file() for name in PDF_NAMES)


def pgvector_needs_reingest(data_dir: Path) -> bool:
    if not pgvector_configured():
        return False
    data_dir = data_dir.resolve()
    with httpx.Client(timeout=60.0) as client:
        chunk_n = _count_chunks(client, INDEX_PROFILE)
    # Produção (Railway): PDFs não vão no volume — índice só via build_rag_pgvector.py
    if not _pdfs_available_in(data_dir):
        return chunk_n == 0
    fp_now = _rag_pdf_manifest_fingerprint(data_dir)
    with httpx.Client(timeout=60.0) as client:
        stored_fp = _get_meta(client, _META_FINGERPRINT_KEY)
        stored_profile = _get_meta(client, _META_PROFILE_KEY)
        if stored_fp != fp_now or stored_profile != INDEX_PROFILE:
            return True
        return chunk_n == 0


def ingest_pgvector_documents(data_dir: Path) -> int:
    if not pgvector_configured():
        raise RuntimeError("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY para RAG pgvector.")

    data_dir = data_dir.resolve()
    if not _pdfs_available_in(data_dir):
        raise RuntimeError(
            "Nenhum PDF institucional em data_dir. "
            "Indexe a partir do PC: python scripts/build_rag_pgvector.py"
        )
    batch = effective_chroma_add_batch()
    total_used = 0
    rows_buffer: list[dict[str, Any]] = []

    with httpx.Client(timeout=120.0) as client:
        _delete_profile_chunks(client, INDEX_PROFILE)

        for pdf_name in PDF_NAMES:
            if total_used >= MAX_CHUNKS_TOTAL:
                break
            pdf_path = data_dir / pdf_name
            if not pdf_path.exists():
                continue
            skip_pages = PPP_SKIP_FIRST_PAGES if pdf_name == PPP_PEDAGOGICO_PDF else 0
            full_text = extract_pdf_text(pdf_path, skip_first_pages=skip_pages)
            cap = min(MAX_CHUNKS_PER_PDF, MAX_CHUNKS_TOTAL - total_used)
            chunks = chunk_pdf_for_index(full_text, cap)
            if not chunks:
                continue

            for i in range(0, len(chunks), batch):
                part = chunks[i : i + batch]
                texts = [_rag_text_for_embedding_index(ch) for ch in part]
                embeddings = _embed_texts(texts)
                for j, (ch, emb) in enumerate(zip(part, embeddings)):
                    idx = i + j
                    rows_buffer.append(
                        {
                            "source": pdf_name,
                            "chunk_index": idx,
                            "content": ch,
                            "embedding": emb,
                            "metadata": {"source": pdf_name, "chunk": str(idx)},
                            "index_profile": INDEX_PROFILE,
                        }
                    )
                if len(rows_buffer) >= 20:
                    _flush_chunks(client, rows_buffer)
                    rows_buffer.clear()

            total_used += len(chunks)
            if ROTINA_API_PAUSE_BETWEEN_PDF_SEC > 0:
                time.sleep(ROTINA_API_PAUSE_BETWEEN_PDF_SEC)

        if rows_buffer:
            _flush_chunks(client, rows_buffer)

        fp = _rag_pdf_manifest_fingerprint(data_dir)
        _set_meta(client, _META_FINGERPRINT_KEY, fp)
        _set_meta(client, _META_PROFILE_KEY, INDEX_PROFILE)
        _set_meta(client, _META_CHUNK_COUNT_KEY, str(total_used))

    return total_used


def _flush_chunks(client: httpx.Client, rows: list[dict[str, Any]]) -> None:
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/document_chunks",
        headers=_service_headers(),
        json=rows,
    )
    r.raise_for_status()


def ensure_pgvector_index(data_dir: Path) -> int:
    if not pgvector_configured():
        return 0
    data_dir = data_dir.resolve()
    if not _pdfs_available_in(data_dir):
        with httpx.Client(timeout=30.0) as client:
            return _count_chunks(client, INDEX_PROFILE)
    if pgvector_needs_reingest(data_dir):
        return ingest_pgvector_documents(data_dir)
    with httpx.Client(timeout=30.0) as client:
        return _count_chunks(client, INDEX_PROFILE)


def _match_chunks(
    client: httpx.Client,
    query_embedding: list[float],
    fetch_n: int,
    profile: str,
    sources: list[str] | None,
    token: str | None,
) -> list[dict[str, Any]]:
    body: dict[str, Any] = {
        "query_embedding": query_embedding,
        "match_count": fetch_n,
        "filter_profile": profile,
    }
    if sources:
        body["filter_sources"] = sources
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/rpc/match_document_chunks",
        headers=_auth_headers(token),
        json=body,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"match_document_chunks falhou: {r.status_code} {r.text[:300]}")
    data = r.json()
    return data if isinstance(data, list) else []


def retrieve_rag_context_and_chunks_pg(
    question: str,
    k: int | None = None,
    *,
    access_token: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    if not pgvector_configured():
        return (
            "(RAG pgvector não configurado — defina SUPABASE_* no .env ou use ROTINA_RAG_BACKEND=chroma.)",
            [],
        )

    with httpx.Client(timeout=60.0) as client:
        n = _count_chunks(client, INDEX_PROFILE)
        if n == 0:
            return (
                "(Nenhum documento indexado no Supabase. Execute scripts/build_rag_pgvector.py.)",
                [],
            )

        top = k if k is not None else RAG_TOP_K
        top = max(1, top)
        if ROTINA_RAG_DISTANCE_GAP > 0:
            fetch_n = min(n, max(top + 4, top * 3, 10))
        else:
            fetch_n = min(top, n)
        if ROTINA_RAG_LEXICAL_WEIGHT > 0:
            fetch_n = min(n, max(fetch_n, top * 4, 16))

        id_q = is_rag_identity_scope_question(question)
        nut_q = is_rag_nutrition_meals_scope_question(question)
        filter_sources: list[str] | None = None
        if id_q and not nut_q:
            filter_sources = list(RAG_IDENTITY_SOURCES)
        elif nut_q and not id_q:
            filter_sources = list(RAG_NUTRITION_SOURCES)

        q_emb = _embed_texts([question])[0]
        token = access_token or SERVICE_KEY
        rows = _match_chunks(
            client, q_emb, fetch_n, INDEX_PROFILE, filter_sources, token
        )
        if filter_sources and not rows:
            rows = _match_chunks(client, q_emb, fetch_n, INDEX_PROFILE, None, token)

    docs = [str(r.get("content") or "") for r in rows]
    dists = [float(r.get("distance") or 0.0) for r in rows]
    metas = [
        {
            **(r.get("metadata") if isinstance(r.get("metadata"), dict) else {}),
            "source": r.get("source", "?"),
            "chunk": str(r.get("chunk_index", "")),
        }
        for r in rows
    ]
    return select_rag_chunks_from_candidates(question, docs, metas, dists, k=k)
