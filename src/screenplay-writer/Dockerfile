# Use official Python runtime as base image
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

COPY src/ ./src/
COPY tests/ ./tests/

# Create directory for output files
RUN mkdir -p /app/output

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.movie_pipeline.api:app", "--host", "0.0.0.0", "--port", "8000"]
