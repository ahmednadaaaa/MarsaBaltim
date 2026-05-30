# ==========================================
# STAGE 1: Build dependencies in virtualenv
# ==========================================
FROM python:3.11-slim-bookworm AS builder

# Set shell and environment options
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system compilation dependencies required for building psycopg2 / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up Python virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# ==========================================
# STAGE 2: Lightweight production runner
# ==========================================
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies (e.g., libpq for PostgreSQL, jpeg for Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy codebase
COPY . .

# Create a non-root system user and configure file ownership for safety
RUN useradd -u 8888 -U -d /app -s /bin/bash django && \
    chown -R django:django /app /opt/venv

# Run the container as the non-root 'django' user
USER django

# Expose Gunicorn's default port
EXPOSE 8000

# Start Gunicorn server
CMD ["gunicorn", "--config", "gunicorn.conf.py", "core.wsgi:application"]
