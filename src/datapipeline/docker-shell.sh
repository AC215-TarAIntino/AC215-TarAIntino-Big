#!/usr/bin/env bash
# Start an interactive shell inside the rag-pipeline container.
# Optionally ensures a Chroma server is running (HTTP) and wires mounts/creds.

set -euo pipefail

########## Config ##########
IMAGE="rag-pipeline"
DOCKERFILE="src/datapipeline/Dockerfile"
PROJECT_DEFAULT="llm-service-account-474620"

# GCS defaults
BUCKET_DEFAULT="${GCS_BUCKET:-tag-genome-data}"
PREFIX_DEFAULT="${GCS_PREFIX:-datasets/tag_genome}"
TAG_REL_OBJECT_DEFAULT="${TAG_REL_OBJECT:-datasets/tag_genome/tag_relevance.dat}"

# Host dirs (quoted to support spaces)
DATA_HOST_DIR="${DATA_HOST_DIR:-$PWD/src/dataweb/tag-genome}"   # -> /app/local-ds (ro)
LOG_HOST_DIR="${LOG_HOST_DIR:-$PWD/src/datapipeline/logs}"      # -> /app/logs (rw)
mkdir -p "$DATA_HOST_DIR" "$LOG_HOST_DIR"

# Chroma server config (HTTP)
AUTO_START_CHROMA="${AUTO_START_CHROMA:-0}"                      # set to 1 to auto-start server
CHROMA_CONTAINER_NAME="${CHROMA_CONTAINER_NAME:-chroma}"
CHROMA_IMAGE="${CHROMA_IMAGE:-ghcr.io/chroma-core/chroma:latest}"
CHROMA_PORT="${CHROMA_PORT:-8000}"

# The app will call the host's Chroma via this host:port
CHROMA_SERVER_HOST_DEFAULT="${CHROMA_SERVER_HOST:-host.docker.internal}"
CHROMA_SERVER_PORT_DEFAULT="${CHROMA_SERVER_PORT:-$CHROMA_PORT}"

CHROMA_COLLECTION="${CHROMA_COLLECTION:-movie_tag_relevance_cos}"
BATCH_SIZE="${BATCH_SIZE:-2000}"
############################

# Build app image if missing
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[build] $IMAGE not found – building…"
  docker build -t "$IMAGE" -f "$DOCKERFILE" .
fi

# Optionally ensure a Chroma server is running on the host
if [[ "$AUTO_START_CHROMA" == "1" ]]; then
  if ! docker ps --format '{{.Names}}' | grep -qx "$CHROMA_CONTAINER_NAME"; then
    if docker ps -a --format '{{.Names}}' | grep -qx "$CHROMA_CONTAINER_NAME"; then
      echo "[chroma] Starting existing container '$CHROMA_CONTAINER_NAME'..."
      docker start "$CHROMA_CONTAINER_NAME" >/dev/null
    else
      echo "[chroma] Running new Chroma server '$CHROMA_CONTAINER_NAME' on :$CHROMA_PORT ..."
      docker run -d --name "$CHROMA_CONTAINER_NAME" -p "$CHROMA_PORT:8000" \
        -e CHROMA_SERVER_HOST=0.0.0.0 \
        -e CHROMA_SERVER_HTTP_PORT=8000 \
        "$CHROMA_IMAGE" >/dev/null
    fi
  fi
fi

# Wait until Chroma is reachable (accept any HTTP response)
# Some images 404 /api/v1/, so probe heartbeat/version.
probe_ok() {
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$CHROMA_PORT/api/v1/heartbeat" || true)
  [[ -n "$code" && "$code" -ge 200 && "$code" -lt 500 ]] && return 0
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$CHROMA_PORT/api/v1/version" || true)
  [[ -n "$code" && "$code" -ge 200 && "$code" -lt 500 ]]
}

echo -n "[chroma] Waiting for http://localhost:$CHROMA_PORT/api/v1/heartbeat ..."
for i in {1..30}; do
  if command -v curl >/dev/null 2>&1 && probe_ok; then
    echo " up."
    break
  fi
  sleep 1
  echo -n "."
  if [[ $i -eq 30 ]]; then
    echo
    echo "!! Chroma did not become ready on localhost:$CHROMA_PORT"
    docker logs --tail=200 "$CHROMA_CONTAINER_NAME" || true
    exit 1
  fi
done

# Credentials picker (ADC > Service Account)
ADC="$HOME/.config/gcloud/application_default_credentials.json"
SA_JSON="$PWD/secrets/llm-service-account.json"
if [[ -f "$ADC" ]]; then
  CRED_PATH="/app/adc.json"; CRED_MOUNT="-v $ADC:$CRED_PATH:ro"
elif [[ -f "$SA_JSON" ]]; then
  CRED_PATH="/app/sa.json"; CRED_MOUNT="-v $SA_JSON:$CRED_PATH:ro"
else
  echo "No GCP creds found."
  echo "  - Run: gcloud auth application-default login (recommended)"
  echo "  - Or place SA key at: $SA_JSON"
  exit 1
fi

# Defaults (can be overridden before calling this script)
PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_DEFAULT}"
BUCKET="${GCS_BUCKET:-$BUCKET_DEFAULT}"
PREFIX="${GCS_PREFIX:-$PREFIX_DEFAULT}"
TAG_REL_OBJECT="${TAG_REL_OBJECT:-$TAG_REL_OBJECT_DEFAULT}"

echo "[info] Project                  : $PROJECT"
echo "[info] Bucket                   : $BUCKET"
echo "[info] Prefix                   : $PREFIX"
echo "[info] Tag file object          : $TAG_REL_OBJECT"
echo "[info] Local DS (ro)            : $DATA_HOST_DIR -> /app/local-ds"
echo "[info] Logs (rw)                : $LOG_HOST_DIR -> /app/logs"
echo "[info] Creds in container       : $CRED_PATH"
echo "[info] Chroma server (HTTP)     : ${CHROMA_SERVER_HOST_DEFAULT}:${CHROMA_SERVER_PORT_DEFAULT}"
echo "[info] Chroma collection        : $CHROMA_COLLECTION"
echo "[info] Batch size               : $BATCH_SIZE"

# NOTE: --add-host below helps Linux resolve host.docker.internal to the host gateway.
exec docker run --rm -it \
  --add-host=host.docker.internal:host-gateway \
  -e GOOGLE_CLOUD_PROJECT="$PROJECT" \
  -e GOOGLE_CLOUD_QUOTA_PROJECT="$PROJECT" \
  -e GOOGLE_APPLICATION_CREDENTIALS="$CRED_PATH" \
  -e GCS_BUCKET="$BUCKET" \
  -e GCS_PREFIX="$PREFIX" \
  -e TAG_REL_OBJECT="$TAG_REL_OBJECT" \
  -e CHROMA_SERVER_HOST="$CHROMA_SERVER_HOST_DEFAULT" \
  -e CHROMA_SERVER_PORT="$CHROMA_SERVER_PORT_DEFAULT" \
  -e CHROMA_COLLECTION="$CHROMA_COLLECTION" \
  -e BATCH_SIZE="$BATCH_SIZE" \
  -e LOG_DIR="/app/logs" \
  -v "$LOG_HOST_DIR:/app/logs" \
  $CRED_MOUNT \
  -v "$DATA_HOST_DIR:/app/local-ds:ro" \
  "$IMAGE" \
  bash

