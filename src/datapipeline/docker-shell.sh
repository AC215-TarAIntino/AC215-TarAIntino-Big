#!/usr/bin/env bash
# Start an interactive shell inside the rag-pipeline container.
# Mounts local data and a persistent Chroma store, and wires GCP credentials.

set -euo pipefail

############################
# Config you can tweak     #
############################
IMAGE="rag-pipeline"
DOCKERFILE="src/datapipeline/Dockerfile"
PROJECT_DEFAULT="llm-service-account-474620"

# GCS defaults
BUCKET_DEFAULT="${GCS_BUCKET:-tag-genome-data}"
PREFIX_DEFAULT="${GCS_PREFIX:-datasets/tag_genome}"
TAG_REL_OBJECT_DEFAULT="${TAG_REL_OBJECT:-datasets/tag_genome/tag_relevance.dat}"

# Host dirs (quoted to support spaces)
DATA_HOST_DIR="${DATA_HOST_DIR:-$PWD/src/dataweb/tag-genome}"            # -> /app/local-ds (ro)
CHROMA_HOST_DIR="${CHROMA_HOST_DIR:-$PWD/src/datapipeline/chroma_db}"    # -> /app/chroma_db (rw, persistent)
LOG_HOST_DIR="${LOG_HOST_DIR:-$PWD/src/datapipeline/logs}"
mkdir -p "$LOG_HOST_DIR"

# Chroma (in-container paths / env defaults)
CHROMA_PATH_IN_CONTAINER="/app/chroma_db"
CHROMA_COLLECTION="${CHROMA_COLLECTION:-movie_tag_relevance_cos}"
BATCH_SIZE="${BATCH_SIZE:-2000}"
############################

# Build image if missing
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[build] $IMAGE not found – building…"
  docker build -t "$IMAGE" -f "$DOCKERFILE" .
fi

# Credentials picker (ADC > Service Account)
ADC="$HOME/.config/gcloud/application_default_credentials.json"
SA_JSON="$PWD/secrets/llm-service-account.json"
if [[ -f "$ADC" ]]; then
  CRED_PATH="/app/adc.json"
  CRED_MOUNT="-v $ADC:$CRED_PATH:ro"
elif [[ -f "$SA_JSON" ]]; then
  CRED_PATH="/app/sa.json"
  CRED_MOUNT="-v $SA_JSON:$CRED_PATH:ro"
else
  echo "No GCP creds found."
  echo "  - Run: gcloud auth application-default login   (recommended)"
  echo "  - Or place SA key at: $SA_JSON"
  exit 1
fi

# Ensure host dirs exist
mkdir -p "$DATA_HOST_DIR" "$CHROMA_HOST_DIR"

# Defaults (can be overridden before calling this script)
PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_DEFAULT}"
BUCKET="${GCS_BUCKET:-$BUCKET_DEFAULT}"
PREFIX="${GCS_PREFIX:-$PREFIX_DEFAULT}"
TAG_REL_OBJECT="${TAG_REL_OBJECT:-$TAG_REL_OBJECT_DEFAULT}"

echo "[info] Project                : $PROJECT"
echo "[info] Bucket                 : $BUCKET"
echo "[info] Prefix                 : $PREFIX"
echo "[info] Tag file object        : $TAG_REL_OBJECT"
echo "[info] Local DS (ro)          : $DATA_HOST_DIR -> /app/local-ds"
echo "[info] Chroma (rw)            : $CHROMA_HOST_DIR -> $CHROMA_PATH_IN_CONTAINER"
echo "[info] Creds in container     : $CRED_PATH"
echo "[info] Chroma collection      : $CHROMA_COLLECTION"
echo "[info] Batch size             : $BATCH_SIZE"

# Launch container
exec docker run --rm -it \
  -e GOOGLE_CLOUD_PROJECT="$PROJECT" \
  -e GOOGLE_CLOUD_QUOTA_PROJECT="$PROJECT" \
  -e GOOGLE_APPLICATION_CREDENTIALS="$CRED_PATH" \
  -e GCS_BUCKET="$BUCKET" \
  -e GCS_PREFIX="$PREFIX" \
  -e TAG_REL_OBJECT="$TAG_REL_OBJECT" \
  -e CHROMA_PATH="$CHROMA_PATH_IN_CONTAINER" \
  -e CHROMA_COLLECTION="$CHROMA_COLLECTION" \
  -e BATCH_SIZE="$BATCH_SIZE" \
  -e LOG_DIR="/app/logs" \
  -v "$LOG_HOST_DIR:/app/logs" \
  $CRED_MOUNT \
  -v "$DATA_HOST_DIR:/app/local-ds:ro" \
  -v "$CHROMA_HOST_DIR:$CHROMA_PATH_IN_CONTAINER" \
  "$IMAGE" \
  bash
