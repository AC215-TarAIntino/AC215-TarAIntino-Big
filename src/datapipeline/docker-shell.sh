#!/usr/bin/env bash
# Start an interactive shell inside the rag-pipeline container
# Chooses ADC if available; otherwise uses service-account key if present.

set -euo pipefail

# ---- config you can tweak ----
IMAGE="rag-pipeline"
DOCKERFILE="src/datapipeline/Dockerfile"   # build context is repo root
PROJECT_DEFAULT="llm-service-account-474620"
BUCKET_DEFAULT="${GCS_BUCKET:-tag-genome-data}"
PREFIX_DEFAULT="${GCS_PREFIX:-datasets/tag_genome}"
DATA_HOST_DIR="${DATA_HOST_DIR:-$PWD/src/dataweb/tag-genome}"   # host dir to mount at /app/local-ds
# -------------------------------

# build image if missing
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[build] $IMAGE not found – building…"
  docker build -t "$IMAGE" -f "$DOCKERFILE" .
fi

# pick credentials: prefer ADC if file exists, else SA JSON
ADC="$HOME/.config/gcloud/application_default_credentials.json"
SA_JSON="$PWD/secrets/llm-service-account.json"

CRED_PATH=""
CRED_MOUNT=""
if [[ -f "$ADC" ]]; then
  CRED_PATH="/app/adc.json"
  CRED_MOUNT="-v $ADC:$CRED_PATH:ro"
elif [[ -f "$SA_JSON" ]]; then
  CRED_PATH="/app/secrets/llm-service-account.json"
  CRED_MOUNT="-v $PWD/secrets:/app/secrets:ro"
else
  echo "!! No credentials found."
  echo "   - For ADC: run 'gcloud auth application-default login' (recommended), or"
  echo "   - Put service-account JSON at: $SA_JSON"
  exit 1
fi

# ensure data dir exists (ok if empty)
mkdir -p "$DATA_HOST_DIR"

# default env (can be overridden before running this script)
PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_DEFAULT}"
BUCKET="${GCS_BUCKET:-$BUCKET_DEFAULT}"
PREFIX="${GCS_PREFIX:-$PREFIX_DEFAULT}"

echo "[info] Using project: $PROJECT"
echo "[info] Using bucket : $BUCKET"
echo "[info] Using prefix : $PREFIX"
echo "[info] Mounting data from: $DATA_HOST_DIR"
echo "[info] Creds at: $CRED_PATH"

# drop into an interactive shell inside the container
exec docker run --rm -it \
  -e GOOGLE_CLOUD_PROJECT="$PROJECT" \
  -e GOOGLE_APPLICATION_CREDENTIALS="$CRED_PATH" \
  -e GCS_BUCKET="$BUCKET" \
  -e GCS_PREFIX="$PREFIX" \
  $CRED_MOUNT \
  -v "$DATA_HOST_DIR:/app/local-ds:ro" \
  -v "$PWD/data:/app/data" \
  "$IMAGE" \
  bash
