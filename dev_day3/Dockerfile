# Dockerfile — Multi-stage build for Mini ASM Python backend
# Stage 1: Builder
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim
LABEL maintainer="Mini ASM Project"

# Install curl (healthcheck) and tini (signal handling)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY . .

# Create data directory for SQLite (used when DB_DRIVER=sqlite)
RUN mkdir -p /data && chmod 777 /data
ENV SQLITE_PATH=/data/mini_asm.db

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "app.py"]
