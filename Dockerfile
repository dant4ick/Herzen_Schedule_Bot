# syntax=docker/dockerfile:1.7
FROM python:3.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

# Create venv for smaller final image (no dev headers kept)
RUN python -m venv /opt/venv

WORKDIR /app

ENV PYTHONPATH=/app

# System deps (if in future need libcurl or others add here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY run.py ./
COPY data ./data
COPY scripts ./scripts

# Create volume point for sqlite db (will be created inside data/)
VOLUME ["/app/data"]

# Expose web app port (default 5000) - for webhook server
EXPOSE 5000

# Healthcheck: simple python expression trying import and exit
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD \
    python -c "import os,sys;print('health');sys.exit(0 if os.getenv('TELEGRAM_TOKEN') else 1)"

# Default env example (override in runtime)
ENV WEBAPP_HOST=0.0.0.0 \
    WEBAPP_PORT=5000

# Run (no debug by default). Add --debug via CMD override if needed.
CMD ["python", "run.py"]
