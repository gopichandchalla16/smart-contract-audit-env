# Smart Contract Audit Environment
# Using ghcr.io mirror to bypass Docker Hub rate limiting on validator
FROM ghcr.io/huggingface/text-generation-inference:sha-ff50a2d-amd64 AS base

# Simpler: use official Python from alternative registry
FROM python:3.9-slim

WORKDIR /app

# Install dependencies as root first
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for HF Spaces
RUN useradd -m -u 1000 user
COPY --chown=user . /app
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
