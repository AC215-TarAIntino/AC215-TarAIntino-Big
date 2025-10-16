# src/llm/Dockerfile
FROM python:3.11-slim-bookworm

# Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# System deps
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create user + app directory
RUN useradd -ms /bin/bash app && mkdir -p /app && chown app:app /app
USER app
WORKDIR /app

# Copy project metadata and install deps with pip
COPY --chown=app:app src/llm/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install -e .

# Copy source code
COPY --chown=app:app src/llm/ /app/

# Default command
CMD ["bash"]
