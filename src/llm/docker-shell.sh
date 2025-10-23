#!/usr/bin/env bash
# Start an interactive shell inside the Vertex AI Gemini container

set -euo pipefail

IMAGE="taraintino-llm"
DOCKERFILE="Dockerfile"
PROJECT_DEFAULT="llm-service-account-474620"

# Get the project root (parent directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DATA_HOST_DIR="${DATA_HOST_DIR:-$PROJECT_ROOT/data}"
LOG_HOST_DIR="${LOG_HOST_DIR:-$PWD/logs}"
mkdir -p "$LOG_HOST_DIR"

# Build the image if missing
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[build] $IMAGE not found – building…"
  docker build -t "$IMAGE" -f "$DOCKERFILE" .
fi

# Locate credentials at project root
SA_JSON="$PROJECT_ROOT/secrets/llm-service-account.json"

if [[ ! -f "$SA_JSON" ]]; then
  echo "!! No credentials found."
  echo "   Please add service account JSON at: $SA_JSON"
  exit 1
fi

CRED_PATH="/app/secrets/llm-service-account.json"
CRED_MOUNT="-v $PROJECT_ROOT/secrets:/app/secrets:ro"

PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_DEFAULT}"

echo "[info] Using project: $PROJECT"
echo "[info] Creds: $CRED_PATH"

exec docker run --rm -it \
  -e GOOGLE_CLOUD_PROJECT="$PROJECT" \
  -e GOOGLE_APPLICATION_CREDENTIALS="$CRED_PATH" \
  -e LOCATION="us-central1" \
  -e MODEL="gemini-2.5-pro" \
  $CRED_MOUNT \
  -v "$DATA_HOST_DIR:/app/local-ds" \
  -e LOG_DIR="/app/logs" \
  -v "$LOG_HOST_DIR:/app/logs" \
  "$IMAGE"