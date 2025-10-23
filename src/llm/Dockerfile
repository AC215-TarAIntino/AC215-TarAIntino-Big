# src/llm/Dockerfile
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install uv

RUN useradd -ms /bin/bash app && mkdir -p /app && chown app:app /app
USER app
WORKDIR /app

COPY --chown=app:app . ./

RUN uv sync
ENTRYPOINT ["/bin/bash"]
CMD ["-c", "source .venv/bin/activate && exec bash"]