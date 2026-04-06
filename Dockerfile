# OpenEnv Smart Contract Audit Environment
# https://huggingface.co/docs/hub/spaces-sdks-docker
FROM python:3.10-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

EXPOSE 7860

# Healthcheck: ping /health every 30s, restart container if it fails 3 times
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--timeout-keep-alive", "30"]
