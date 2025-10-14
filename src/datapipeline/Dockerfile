# src/datapipeline/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Dependencies (copy from repo root when building with context ".")
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Pipeline code
COPY src/datapipeline /app/datapipeline

# Python module path
ENV PYTHONPATH=/app

# Default credential path (we'll mount the real file at runtime)
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/llm-service-account.json

# Show help by default
CMD ["python", "datapipeline/dataloader.py", "--help"]
