# Pipeline2 Setup Guide - Complete Local Testing

This guide walks you through setting up and running `pipeline2.py` - the full orchestration pipeline that generates movie trailers from taste vectors.

## Overview

Pipeline2 orchestrates all microservices to generate a complete movie trailer:
```
taste_vector → movie concept → trailer breakdown → video generation → GCS upload
```

**Services involved:**
1. `screenplay-writer` - Generates movie concepts
2. `scene-decomposer` - Creates trailer scene breakdowns
3. `video-generator` - Generates videos using Google Gemini/VEO
4. `quiz-vector` - (Optional) Provides taste vectors
5. `chroma` - Vector database for recommendations

---

## Prerequisites

### 1. Required API Keys

You need the following API keys:

#### OpenRouter API Key
Used by screenplay-writer and scene-decomposer for LLM generation.

1. Visit https://openrouter.ai/keys
2. Sign up and create an API key
3. Copy the key (starts with `sk-or-v1-...`)

#### OMDb API Key
Used by screenplay-writer for movie metadata.

1. Visit http://www.omdbapi.com/apikey.aspx
2. Sign up for free tier
3. Copy the API key

#### Google Gemini API Key
Used by video-generator for image and video generation with VEO 3.1.

**Option A: Google AI Studio (Recommended)**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API key in new project"
3. Copy the API key (starts with `AIza...`)

**Option B: Google Cloud Console**
1. Visit https://console.cloud.google.com/
2. Create a new project
3. Enable "Generative Language API":
   - Go to https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - Click "Enable"
4. Create credentials:
   - Go to https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key

#### Google Cloud Service Account (for GCS upload)
1. Visit https://console.cloud.google.com/
2. Navigate to "IAM & Admin" → "Service Accounts"
3. Click "Create Service Account"
4. Grant "Storage Admin" role
5. Create and download JSON key file
6. Save as `tarantaino-key.json` (or similar)

---

## Installation Steps

### Step 1: Clone and Navigate to Project

```bash
cd "/Users/robertdebbas/Desktop/MSc/Adv Pra Data Science /Projects/AC215-TarAIntino-Big"
```

### Step 2: Configure Environment Variables

Create/update the `.env` file in the project root:

```bash
cat > .env << 'EOF'
# =============================================================================
# TarAIntino - Environment Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# OpenRouter API Configuration (for LLM services)
# -----------------------------------------------------------------------------
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
OPENROUTER_MODEL=anthropic/claude-3-haiku

# -----------------------------------------------------------------------------
# OMDb API Configuration (for screenplay-writer)
# -----------------------------------------------------------------------------
OMDB_API_KEY=YOUR_KEY_HERE

# -----------------------------------------------------------------------------
# Google Cloud Configuration
# -----------------------------------------------------------------------------
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourusername/path/to/tarantaino-key.json
GCS_BUCKET_NAME=tarantaino-output
GCS_PREFIX=video_generator_outputs

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------
DEFAULT_TRAILER_DURATION=35
INCLUDE_NARRATION=true
API_HOST=0.0.0.0
API_PORT=8000

# -----------------------------------------------------------------------------
# ChromaDB Configuration
# -----------------------------------------------------------------------------
CHROMA_SERVER_HOST=chroma
CHROMA_SERVER_PORT=8000
CHROMA_COLLECTION=movie_tag_relevance_cos
ALLOW_RESET=true

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_DIR=/app/datapipeline/logs
EOF
```

**Important:** Replace the following placeholders:
- `YOUR_KEY_HERE` with your actual API keys
- `your-project-id` with your Google Cloud project ID
- `/Users/yourusername/path/to/tarantaino-key.json` with actual path to your service account key

### Step 3: Configure Video Generator Secret

The video-generator service needs a separate `secret.json` file for Gemini API access:

```bash
cd Video_Generator

cat > secret.json << 'EOF'
{
  "project_api_key": "YOUR_GEMINI_API_KEY_HERE"
}
EOF

cd ..
```

**Replace** `YOUR_GEMINI_API_KEY_HERE` with your actual Gemini API key from Step 1.

**Security Note:** This file is already in `.gitignore` and will not be committed.

### Step 4: Create GCS Bucket

If you haven't created the GCS bucket yet:

```bash
# Set your project
gcloud config set project your-project-id

# Create bucket
gsutil mb -l us-central1 gs://tarantaino-output

# Verify
gsutil ls gs://tarantaino-output
```

---

## Running the Pipeline

### Step 1: Start All Services

```bash
docker-compose up -d
```

This starts:
- `screenplay-writer` (port 8080)
- `scene-decomposer` (port 8001)
- `video-generator` (port 8003)
- `quiz-vector` (port 8082)
- `chroma` (port 8000)

### Step 2: Verify Services are Healthy

```bash
# Check all services are running
docker-compose ps

# Check health endpoints
curl http://localhost:8080/health  # screenplay-writer
curl http://localhost:8001/health  # scene-decomposer
curl http://localhost:8003/health  # video-generator
```

All should return `{"status":"ok"}` or similar.

### Step 3: Run Test Pipeline

Test the full pipeline with a simple script:

```bash
python test_full_simple.py
```

**Expected output:**
```
🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬
SIMPLE FULL PIPELINE TEST
Testing: Movie -> Trailer -> Video -> GCS
🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬🎬

📝 Step 1/4: Generating movie concept...
✅ Generated: [Movie Title]
   Genres: [Genres]...

🎬 Step 2/4: Generating trailer breakdown...
✅ Generated 6 scenes with 4 characters

🎥 Step 3/4: Generating video...
   This may take several minutes...
✅ Video generated: [path]

☁️  Step 4/4: Uploading to GCS...
✅ Uploaded to: gs://tarantaino-output/trailers/trailer_[timestamp].mp4

🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!
```

**Note:** Step 3 (video generation) can take 5-15 minutes as it generates:
- 4 character reference images
- 6 scene videos (each 4-8 seconds)
- Final stitched trailer

### Step 4: Run Pipeline2 Programmatically

Use `pipeline2.py` in your code:

```python
from pipeline2 import generate_trailer

# Example taste vector (1100 dimensions)
taste_vector = [0.5] * 1100

# Generate trailer
result = generate_trailer(
    taste_vector=taste_vector,
    custom_prompt="Create an epic sci-fi thriller with stunning visuals"
)

# Check result
if result['success']:
    print(f"✅ Success! Video URL: {result['gcs_url']}")
    print(f"Local path: {result['local_video_path']}")
else:
    print(f"❌ Failed: {result['error']}")
```

---

## Troubleshooting

### Issue: "Step 2 failed: 'NoneType' object has no attribute 'get'"

**Cause:** Scene-decomposer is returning an error response due to validation failure.

**Solution:**
1. Check scene-decomposer logs: `docker-compose logs scene-decomposer --tail=50`
2. Common issues:
   - LLM generating invalid scene durations (must be 4-10 seconds)
   - JSON parsing errors from LLM response
3. Rebuild service: `docker-compose up -d --build scene-decomposer`

### Issue: "Step 3 failed: 500 Server Error"

**Cause:** Video-generator cannot access Gemini API.

**Solution:**
1. Verify `Video_Generator/secret.json` exists and contains valid API key
2. Check if VEO 3.1 is enabled for your API key:
   - Visit https://labs.google/veo to request access
   - Or try generating a test image in Google AI Studio to verify key works
3. Check logs: `docker logs video-generator --tail=50`
4. Restart service: `docker-compose restart video-generator`

### Issue: "Step 3 failed: Read timed out"

**Cause:** Video generation takes longer than 10-minute timeout.

**Solution:** This is expected for complex trailers. Options:
1. Increase timeout in `test_full_simple.py` line 106 (change from 600 to 1200)
2. Reduce trailer duration in Step 2 (use `target_duration: 20` instead of `35`)
3. Check video-generator logs to see progress: `docker logs video-generator --follow`

### Issue: "Step 4 failed: Could not initialize GCS client"

**Cause:** Google Cloud credentials not configured.

**Solution:**
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` path in `.env` is correct
2. Check file exists: `ls -la /path/to/tarantaino-key.json`
3. Verify file has correct permissions (readable)
4. Test manually:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   python -c "from google.cloud import storage; print(storage.Client().project)"
   ```

### Issue: Services won't start / Port conflicts

**Cause:** Ports already in use.

**Solution:**
1. Check what's using the ports:
   ```bash
   lsof -i :8080  # screenplay-writer
   lsof -i :8001  # scene-decomposer
   lsof -i :8003  # video-generator
   ```
2. Stop conflicting services or change ports in `docker-compose.yml`

---

## Service-Specific Debugging

### Screenplay-Writer Logs
```bash
docker-compose logs screenplay-writer --tail=50 --follow
```

**Common issues:**
- Missing OMDB API key
- Invalid OpenRouter API key
- Movie not found in OMDB database

### Scene-Decomposer Logs
```bash
docker-compose logs scene-decomposer --tail=50 --follow
```

**Common issues:**
- JSON parsing errors from LLM
- Invalid scene duration (must be 4-10 seconds)
- Missing character designs

### Video-Generator Logs
```bash
docker logs video-generator --tail=100 --follow
```

**Common issues:**
- Missing `secret.json` file
- Invalid Gemini API key
- VEO 3.1 not enabled for API key
- Rate limits exceeded

---

## Performance Notes

### Expected Timing
- **Step 1 (Movie Generation):** ~10-20 seconds
- **Step 2 (Trailer Breakdown):** ~30-60 seconds
- **Step 3 (Video Generation):** 5-15 minutes
  - Character reference generation: ~2-3 minutes (4 characters)
  - Scene video generation: ~3-10 minutes (6 scenes)
  - Video stitching: ~10-30 seconds
- **Step 4 (GCS Upload):** ~5-10 seconds

### Resource Requirements
- **RAM:** Minimum 8GB, recommended 16GB
- **Disk:** ~2GB for Docker images, ~500MB per generated trailer
- **Network:** Stable internet connection for API calls

---

## API Rate Limits

### OpenRouter
- Free tier: Varies by model
- Claude Haiku: Generally generous limits
- Monitor usage at https://openrouter.ai/activity

### Google Gemini
- Free tier: 60 requests per minute
- VEO video generation: Rate limited (check current limits)
- Monitor quota at https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

---

## Files Modified During This Setup

### Core Files Created/Modified
1. `.env` - Environment configuration
2. `Video_Generator/secret.json` - Gemini API credentials
3. `test_full_simple.py` - Test script (updated endpoint)
4. `scene-decomposer/src/trailer_generator/scene_generator.py` - Improved JSON parsing

### Key Fixes Applied
1. **Scene duration validation** - Added explicit 4-10 second constraints
2. **JSON parsing** - Aggressive cleanup for LLM-generated JSON
3. **Test endpoint** - Fixed `/generate-video` → `/generate/trailer`
4. **API key loading** - Proper `secret.json` path

---

## Next Steps

Once the pipeline is working locally:

1. **Test with real taste vectors** from quiz-vector service
2. **Optimize video generation** - experiment with different models/settings
3. **Deploy to Cloud Run** - for production usage
4. **Add monitoring** - track success rates and generation times
5. **Implement caching** - cache character references for faster iteration

---

## Support

If you encounter issues not covered here:

1. Check Docker logs for all services
2. Verify all API keys are valid and have sufficient quota
3. Ensure network connectivity to external APIs
4. Review `.env` configuration for typos

For additional help, contact the team or refer to individual service READMEs.

---

## Summary Checklist

Before running pipeline2, ensure:

- [ ] `.env` file configured with all API keys
- [ ] `Video_Generator/secret.json` created with Gemini API key
- [ ] Google Cloud service account key downloaded and path set
- [ ] GCS bucket created (`tarantaino-output`)
- [ ] All Docker services started (`docker-compose up -d`)
- [ ] All health endpoints responding (`/health`)
- [ ] Test script runs successfully (`python test_full_simple.py`)

**Estimated setup time:** 30-45 minutes (first time)

**Estimated first run time:** 15-20 minutes (including video generation)

---

*Last updated: November 19, 2024*
*Tested on: macOS with Docker Desktop*
