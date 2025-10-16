# src/datapipeline/Dockerfile
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    useradd -ms /bin/bash app && \
    mkdir -p /app && \
    chown app:app /app

USER app
WORKDIR /app
COPY --chown=app:app src/datapipeline/ ./
RUN uv sync

COPY src/datapipeline /app/datapipeline

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["source /app/.venv/bin/activate && exec bash"]
