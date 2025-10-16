#!/usr/bin/env bash
# Start an interactive shell inside the Vertex AI Gemini container

set -euo pipefail

IMAGE="taraintino-llm"
DOCKERFILE="src/llm/Dockerfile"
PROJECT_DEFAULT="llm-service-account-474620"
DATA_HOST_DIR="${DATA_HOST_DIR:-$PWD/data}"

# Build the image if missing
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[build] $IMAGE not found – building…"
  docker build -t "$IMAGE" -f "$DOCKERFILE" .
fi

# Locate credentials
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
  echo "   Run 'gcloud auth application-default login' or add $SA_JSON"
  exit 1
fi

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
  --env-file secrets/.env \
  "$IMAGE" \
  bash
