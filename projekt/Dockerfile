# ── Builder stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps needed to build Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.1.3

COPY pyproject.toml poetry.lock ./

# Install dependencies into a project-local venv (no dev, no root)
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-interaction --no-ansi --no-root

# ── Runtime stage ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime libraries: libmupdf for PyMuPDF text extraction,
# ca-certificates for HTTPS downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Install project source as a package in the venv
COPY src/ ./src/
COPY pyproject.toml README.md ./
RUN /app/.venv/bin/pip install --no-deps -e . > /dev/null

# ── Runtime configuration ──────────────────────────────────────

# XDG paths point into the mountable volumes:
#   /config   → config.toml  (XDG_CONFIG_HOME)
#   /data     → papers.db + pdfs/  (XDG_DATA_HOME)
ENV XDG_CONFIG_HOME=/config
ENV XDG_DATA_HOME=/data
ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /config/paper-aggregator /data/paper-aggregator/pdfs

VOLUME ["/config", "/data"]

ENTRYPOINT ["paper-aggregator"]
CMD ["--help"]
