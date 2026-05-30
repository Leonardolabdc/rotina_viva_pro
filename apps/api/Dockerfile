# syntax=docker/dockerfile:1
# Worker FastAPI — produção (Fase 6). Build a partir da raiz do monorepo:
#   docker build -f apps/api/Dockerfile -t rotina-api .

FROM python:3.12-slim-bookworm

# Railway Hobby: deixar 0 (sem PyTorch). Local/prod com RAM: --build-arg INSTALL_LLM_GUARD=1
ARG INSTALL_LLM_GUARD=0

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src:/app/apps/api \
    ROTINA_DATA_DIR=/data \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app/apps/api

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt /app/requirements-prod.txt
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
COPY apps/api/requirements-supabase.txt /app/apps/api/requirements-supabase.txt
COPY apps/api/requirements-llm-guard.txt /app/apps/api/requirements-llm-guard.txt
COPY apps/api/requirements-worker-railway.txt /app/apps/api/requirements-worker-railway.txt
COPY apps/api/requirements-worker.txt /app/apps/api/requirements-worker.txt

RUN if [ "$INSTALL_LLM_GUARD" = "1" ]; then \
      pip install --no-cache-dir -r requirements-worker.txt; \
    else \
      pip install --no-cache-dir -r requirements-worker-railway.txt; \
    fi

COPY src /app/src
COPY apps/api/rotina_api /app/apps/api/rotina_api
COPY apps/api/run_prod.py /app/apps/api/run_prod.py
COPY packages/api-contracts /app/packages/api-contracts
# Seed embutido na imagem; runtime grava em ROTINA_DATA_DIR (/data = volume Railway)
COPY data /app/seed-data
ENV ROTINA_SEED_DATA_DIR=/app/seed-data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10)" || exit 1

CMD ["python", "run_prod.py"]
