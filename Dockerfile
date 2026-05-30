# syntax=docker/dockerfile:1
# Imagem de produção — Streamlit + DuckDB + ChromaDB (sem torch, sem testes)
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    ROTINA_DATA_DIR=/data \
    CHROMA_PERSIST_DIR=/data/vector_db \
    ROTINA_ENABLE_CREWAI=false \
    ROTINA_ENABLE_ML_LAB=false \
    ROTINA_LANGFUSE_ENABLED=false \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-prod.txt

COPY app.py .
COPY src/ ./src/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5)" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.fileWatcherType=none"]
