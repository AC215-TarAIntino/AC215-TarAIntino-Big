# src/Dockerfile
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/app/src"

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/* \
 && pip install -U pip uv

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

RUN uv sync --extra dev

COPY . /app/

# default shell in case you exec into the container
CMD ["bash", "-lc", "sleep infinity"]