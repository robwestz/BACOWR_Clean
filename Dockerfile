# BACOWR Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 bacowr && \
    mkdir -p /app/output && \
    chown -R bacowr:bacowr /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/bacowr/.local

# Copy application code
COPY --chown=bacowr:bacowr . .

# Switch to non-root user
USER bacowr

# Add local bin to PATH
ENV PATH=/home/bacowr/.local/bin:$PATH

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Default command: run API server
CMD ["uvicorn", "bacowr.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
