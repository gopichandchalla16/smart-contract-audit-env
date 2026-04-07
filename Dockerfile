# OpenEnv Smart Contract Audit Environment
# https://huggingface.co/docs/hub/spaces-sdks-docker

# Using pinned slim-bullseye tag for maximum registry stability
# If docker.io is unreachable, validator can use: ghcr.io/huggingface/patch:3.10-slim
FROM python:3.10-slim-bullseye

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=user . /app

EXPOSE 7860

# Healthcheck: ping /health every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--timeout-keep-alive", "75"]
