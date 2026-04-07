# OpenEnv Smart Contract Audit Environment
# Pinned to python:3.10-slim-bullseye for stable Docker Hub manifest
FROM python:3.10-slim-bullseye

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install Python dependencies first (layer cache optimization)
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user . /app

EXPOSE 7860

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Start server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--timeout-keep-alive", "75"]
