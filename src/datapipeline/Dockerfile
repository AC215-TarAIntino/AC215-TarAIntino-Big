FROM python:3.11-slim

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY src/datapipeline/pyproject.toml pyproject.toml

RUN uv sync --no-dev

COPY src/datapipeline /app/datapipeline

ENV PYTHONPATH=/app \
    RAW_DATA_DIR=/data/raw \
    PROCESSED_DATA_DIR=/data/processed \
    QUERY_DIR=/data/queries \
    ARTIFACT_DIR=/data/artifacts \
    GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/llm-service-account.json

CMD ["uv", "run", "python", "-m", "datapipeline.preprocess_rag"]
