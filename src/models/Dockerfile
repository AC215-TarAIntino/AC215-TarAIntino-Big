FROM python:3.11-slim

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY src/models/pyproject.toml pyproject.toml

RUN uv sync --no-dev

COPY src/models /app/models

ENV PYTHONPATH=/app \
    PROCESSED_DATA_DIR=/data/processed \
    QUERY_DIR=/data/queries \
    OUTPUT_DIR=/outputs \
    ARTIFACT_DIR=/outputs/artifacts

CMD ["uv", "run", "python", "-m", "models.model_rag"]
