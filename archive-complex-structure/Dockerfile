# ATHintel Enterprise Platform - Multi-stage Docker Build
# Production-ready containerization with security and performance optimizations

FROM python:3.11-slim-bookworm AS base

# Metadata
LABEL maintainer="ATHintel Enterprise Team <enterprise@athintel.com>"
LABEL description="Athens Real Estate Intelligence Platform with Advanced 2025 Web Scraping"
LABEL version="2.0.0"

# Environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build dependencies
    build-essential \
    gcc \
    g++ \
    # Browser dependencies for Playwright
    wget \
    gnupg \
    # Database clients
    postgresql-client \
    # Network tools
    curl \
    dnsutils \
    # Security and process management
    tini \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1001 athintel \
    && useradd --uid 1001 --gid athintel --shell /bin/bash --create-home athintel

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* requirements_enterprise_2025.txt ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root \
    && rm -rf $POETRY_CACHE_DIR

# ============================================================================
# Development Stage
# ============================================================================
FROM base AS development

# Install development dependencies
RUN poetry install --no-root \
    && rm -rf $POETRY_CACHE_DIR

# Install Playwright browsers (development only)
RUN playwright install chromium firefox webkit \
    && playwright install-deps

# Copy source code
COPY --chown=athintel:athintel . .

# Install the package in development mode
RUN poetry install

# Switch to non-root user
USER athintel

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development entrypoint
CMD ["uvicorn", "src.cli.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# Production Builder Stage
# ============================================================================
FROM base AS builder

# Copy source code
COPY --chown=athintel:athintel . .

# Install the package
RUN poetry build && \
    pip install dist/*.whl && \
    rm -rf dist/ build/

# Install Playwright browsers for production
RUN playwright install chromium --with-deps

# ============================================================================
# Production Runtime Stage
# ============================================================================
FROM python:3.11-slim-bookworm AS production

# Metadata for production
LABEL stage="production"

# Production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ATHINTEL_ENV=production \
    ATHINTEL_LOG_LEVEL=info

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    # Runtime dependencies for browsers
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    # Database client
    postgresql-client \
    # Process management
    tini \
    # Network tools for health checks
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1001 athintel \
    && useradd --uid 1001 --gid athintel --shell /bin/bash --create-home athintel

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Playwright browsers
COPY --from=builder /home/athintel/.cache/ms-playwright /home/athintel/.cache/ms-playwright

# Create application directory
WORKDIR /app

# Copy only necessary production files
COPY --chown=athintel:athintel src/ src/
COPY --chown=athintel:athintel config/ config/
COPY --chown=athintel:athintel scripts/production/ scripts/
COPY --chown=athintel:athintel --chmod=755 docker/entrypoint.sh /entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/temp /app/reports && \
    chown -R athintel:athintel /app

# Switch to non-root user
USER athintel

# Expose ports
EXPOSE 8000

# Volume mounts for persistent data
VOLUME ["/app/data", "/app/logs", "/app/reports"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]

# Default command
CMD ["athintel", "serve", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Analytics Worker Stage (for distributed processing)
# ============================================================================
FROM production AS analytics-worker

# Analytics worker specific environment
ENV ATHINTEL_WORKER_TYPE=analytics \
    ATHINTEL_QUEUE_URL=redis://redis:6379/0

# Install additional analytics dependencies
USER root
RUN pip install celery[redis]==5.3.6 flower==2.0.1
USER athintel

# Worker command
CMD ["celery", "worker", "-A", "src.core.analytics.tasks", "--loglevel=info", "--concurrency=4"]

# ============================================================================
# Scraper Worker Stage (for web scraping tasks)
# ============================================================================
FROM production AS scraper-worker

# Scraper worker specific environment
ENV ATHINTEL_WORKER_TYPE=scraper \
    ATHINTEL_QUEUE_URL=redis://redis:6379/1 \
    PLAYWRIGHT_BROWSERS_PATH=/home/athintel/.cache/ms-playwright

# Additional browser setup for scraping
USER root

# Install additional browser dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

USER athintel

# Worker command for scraping tasks
CMD ["celery", "worker", "-A", "src.adapters.scrapers.tasks", "--loglevel=info", "--concurrency=2"]

# ============================================================================
# Dashboard Stage (for Streamlit dashboard)
# ============================================================================
FROM production AS dashboard

# Dashboard specific environment
ENV ATHINTEL_SERVICE_TYPE=dashboard \
    STREAMLIT_SERVER_PORT=8501

# Expose Streamlit port
EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# Dashboard command
CMD ["streamlit", "run", "src/adapters/dashboards/executive_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ============================================================================
# Monitoring Stage (for Prometheus metrics)
# ============================================================================
FROM production AS monitoring

# Monitoring specific environment
ENV ATHINTEL_SERVICE_TYPE=monitoring \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_metrics

# Create metrics directory
RUN mkdir -p /tmp/prometheus_metrics && \
    chown athintel:athintel /tmp/prometheus_metrics

# Monitoring command
CMD ["athintel", "monitor", "--metrics-port", "9090"]