# Build stage
FROM python:3.14-slim AS builder

# Prevent Python from writing .pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout/stderr so logs appear immediately.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .
RUN chmod +x entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# EXPOSE is documentation only — Render assigns the real port via $PORT at
# runtime and entrypoint.sh binds gunicorn to it (falls back to 8000 locally).
EXPOSE 8000

# Health check — uses $PORT so it still works when Render remaps it.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD sh -c "curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1"

# Migrate + collectstatic (needs runtime env vars) then start Gunicorn.
ENTRYPOINT ["./entrypoint.sh"]
