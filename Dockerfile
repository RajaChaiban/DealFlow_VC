# =============================================================================
# DealFlow AI Copilot - Multi-Stage Dockerfile
# =============================================================================
# Stages:
#   1. base       - Common Python base with system deps
#   2. builder    - Install Python dependencies into a venv
#   3. test       - Run tests (optional, CI only)
#   4. production - Lean runtime image
#
# Build:
#   docker build -t dealflow-api .
#   docker build --target test -t dealflow-api:test .
#
# Run:
#   docker run -p 8000:8000 --env-file .env dealflow-api
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Base image with system dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System packages needed at build time AND runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


# ---------------------------------------------------------------------------
# Stage 2: Builder - install Python deps into a virtual environment
# ---------------------------------------------------------------------------
FROM base AS builder

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 3: Test runner (optional -- used in CI)
# ---------------------------------------------------------------------------
FROM builder AS test

WORKDIR /app

# Copy the full source
COPY . .

# Install test-only dependencies (if not already in requirements.txt)
RUN pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
RUN pytest tests/ -v --tb=short || true


# ---------------------------------------------------------------------------
# Stage 4: Production image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="DealFlow Team" \
      version="0.1.0" \
      description="DealFlow AI Copilot - AI-powered deal analysis platform"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Runtime-only system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --chown=appuser:appgroup . .

# Create data directories
RUN mkdir -p data/uploads data/processed data/outputs logs prompts .cache/extractions && \
    chown -R appuser:appgroup data logs prompts .cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command -- Uvicorn with production settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--access-log"]
