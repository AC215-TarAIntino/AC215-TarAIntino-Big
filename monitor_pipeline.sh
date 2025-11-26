#!/bin/bash

# Monitor the video generation pipeline in real-time
# Usage: ./monitor_pipeline.sh

echo "🎬 TarAIntino Pipeline Monitor"
echo "================================"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status
print_status() {
    local service=$1
    local status=$2
    local message=$3

    case $status in
        "success")
            echo -e "${GREEN}✅ $service${NC}: $message"
            ;;
        "processing")
            echo -e "${YELLOW}⏳ $service${NC}: $message"
            ;;
        "error")
            echo -e "${RED}❌ $service${NC}: $message"
            ;;
        "info")
            echo -e "${BLUE}ℹ️  $service${NC}: $message"
            ;;
    esac
}

# Monitor logs in real-time
docker-compose logs -f --tail=0 frontend screenplay-writer scene-decomposer video-generator 2>&1 | while read line; do
    # Parse different log types
    if echo "$line" | grep -q "Starting video generation"; then
        SESSION_ID=$(echo "$line" | sed -n 's/.*\[\([0-9a-f-]*\)\].*/\1/p')
        print_status "PIPELINE" "info" "New session started: $SESSION_ID"

    elif echo "$line" | grep -q "Getting recommendations"; then
        print_status "QUIZ SERVICE" "processing" "Fetching movie recommendations..."

    elif echo "$line" | grep -q "Using .* movie recommendations"; then
        MOVIES=$(echo "$line" | sed 's/.*Using //')
        print_status "QUIZ SERVICE" "success" "$MOVIES"

    elif echo "$line" | grep -q "Generating movie concept"; then
        print_status "SCREENPLAY" "processing" "AI is writing the movie concept..."

    elif echo "$line" | grep -q "Movie generated:"; then
        TITLE=$(echo "$line" | sed 's/.*Movie generated: //')
        print_status "SCREENPLAY" "success" "Movie created: '$TITLE'"

    elif echo "$line" | grep -q "Generating trailer breakdown"; then
        print_status "SCENE-DECOMPOSER" "processing" "Breaking down into scenes..."

    elif echo "$line" | grep -q "Trailer breakdown generated"; then
        SCENES=$(echo "$line" | sed 's/.*generated: //')
        print_status "SCENE-DECOMPOSER" "success" "Trailer ready: $SCENES"

    elif echo "$line" | grep -q "Starting video generation"; then
        print_status "VIDEO-GENERATOR" "processing" "Generating AI video (15-20 min)..."

    elif echo "$line" | grep -q "Video generation complete"; then
        print_status "VIDEO-GENERATOR" "success" "Video ready!"

    elif echo "$line" | grep -q "GCS URL:"; then
        GCS=$(echo "$line" | sed 's/.*GCS URL: //')
        print_status "VIDEO-GENERATOR" "success" "Uploaded: $GCS"

    elif echo "$line" | grep -qi "error\|failed"; then
        ERROR=$(echo "$line" | sed 's/^.*ERROR://')
        print_status "ERROR" "error" "$ERROR"

    elif echo "$line" | grep -q "429 Too Many Requests\|rate-limited upstream"; then
        print_status "API" "error" "⚠️  Rate limited! Free model is overloaded. Consider using paid model."
    fi
done
