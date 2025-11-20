# AC215-TarAIntino-Big

A comprehensive MLOps system for generating personalized movie trailers using taste vectors, LLMs, and video generation AI.

## Overview

TarAIntino is an end-to-end machine learning pipeline that creates personalized movie trailers based on user preferences. The system:

- **Analyzes user taste** through an interactive quiz interface
- **Generates movie concepts** using LLM-powered screenplay writing
- **Creates trailer breakdowns** with detailed scene descriptions
- **Produces video content** using Google Gemini/VEO 3.1
- **Delivers results** via a React-based frontend with real-time polling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network: tarantino-network         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   ChromaDB   │────▶│  Quiz RAG    │────▶│ Quiz Service│  │
│  │   :8000      │     │    App       │     │   :8082     │  │
│  └──────────────┘     └──────────────┘     └─────────────┘  │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │ Screenplay   │────▶│    Scene     │────▶│    Video    │  │
│  │   Writer     │     │  Decomposer  │     │  Generator  │  │
│  │   :8080      │     │   :8001      │     │   :8003     │  │
│  └──────────────┘     └──────────────┘     └─────────────┘  │
│                                                             │
│  ┌──────────────┐                                           │
│  │   Frontend   │                                           │
│  │   :3000      │                                           │
│  └──────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
AC215-TarAIntino-Big/
├── .github/
│   └── workflows/                  # CI/CD pipelines
├── quiz-vector/                    # Quiz service and RAG system
│   ├── src/                        # Source code
│   ├── secrets/                    # GCS credentials
│   └── README.md                   # Quiz service documentation
├── screenplay-writer/              # Movie concept generation
│   ├── src/                        # Source code
│   ├── tests/                      # Unit tests
│   ├── outputs/                    # Generated outputs
│   └── README.md                   # Screenplay service docs
├── scene-decomposer/               # Trailer breakdown service
│   ├── src/                        # Source code
│   ├── tests/                      # Unit tests
│   ├── outputs/                    # Generated outputs
│   └── README.md                   # Scene decomposer docs
├── video-generator/                # Video generation service
│   ├── output/                     # Generated videos
│   ├── trailer_breakdown_samples/  # Sample inputs
│   └── secret.json                 # Gemini API credentials
├── frontend/                       # React frontend application
│   ├── app/                        # Next.js app directory
│   ├── components/                 # React components
│   ├── public/                     # Static assets
│   └── README.md                   # Frontend documentation
├── docker-compose.yml              # Service orchestration
├── pipeline2.py                    # Full orchestration pipeline
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies
├── setup.sh                        # Setup script
└── README.md                       # This file
```

## Quick Start

### Prerequisites

- **Docker & Docker Compose** - For containerization
- **Python 3.11+** - For running pipelines
- **Node.js 20+** - For React frontend (optional)
- **Google Cloud SDK** - For GCS deployment (optional)
- **API Keys:**
  - OpenRouter API key (for LLM services)
  - OMDb API key (for movie metadata)
  - Google Gemini API key (for video generation)
  - Google Cloud service account (for GCS upload)

### Installation

#### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd AC215-TarAIntino-Big
```

#### 2. Configure API Keys

Edit `.env` with your credentials:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
OPENROUTER_MODEL=anthropic/claude-3-haiku

# OMDb API Configuration
OMDB_API_KEY=YOUR_KEY_HERE

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=tarantaino-output
GCS_PREFIX=video_generator_outputs

# Service Configuration
DEFAULT_TRAILER_DURATION=35
INCLUDE_NARRATION=true

# ChromaDB Configuration
CHROMA_SERVER_HOST=chroma
CHROMA_SERVER_PORT=8000
CHROMA_COLLECTION=movie_tag_relevance_cos
```

**Get your API keys:**

- **OpenRouter:** https://openrouter.ai/keys
- **OMDb:** http://www.omdbapi.com/apikey.aspx
- **Google Gemini:** https://aistudio.google.com/app/apikey
- **Google Cloud Service Account:** https://console.cloud.google.com/ → IAM & Admin → Service Accounts

#### 3. Configure Service Credentials

**Quiz Vector Service:**
```bash
# Place service account key
cp /path/to/your-key.json quiz-vector/secrets/llm-service-account.json
```

**Video Generator Service:**
```bash
# Create Gemini API config
cat > video-generator/secret.json << 'EOF'
{
  "project_api_key": "YOUR_GEMINI_API_KEY_HERE"
}
EOF
```

**Copy .env to services:**
```bash
cp .env screenplay-writer/.env
cp .env scene-decomposer/.env
```

#### 4. Create GCS Bucket

```bash
# Set your project
gcloud config set project your-project-id

# Create bucket
gsutil mb -l us-central1 gs://tarantaino-output

# Verify
gsutil ls gs://tarantaino-output
```

### Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d

# Check service status
docker-compose ps
```

### Verify Services

```bash
# Check health endpoints
curl http://localhost:8082/health  # Quiz Service
curl http://localhost:8080/health  # Screenplay Writer
curl http://localhost:8001/health  # Scene Decomposer
curl http://localhost:8003/health  # Video Generator
curl http://localhost:3000         # Frontend
```

All should return `{"status":"ok"}` or display the frontend.

## Services

For detailed implementation information, see the README files in each service directory.

### Quiz Service (:8082)
**Interactive quiz and recommendation engine**

- Generate taste vectors from user preferences
- Retrieve movie recommendations using RAG
- Vector database integration with ChromaDB
- See: [quiz-vector/README.md](quiz-vector/README.md)

**Endpoints:**
- `POST /quiz/start` - Start new quiz session
- `POST /quiz/answer` - Submit answer
- `POST /recommend` - Get recommendations from taste vector
- `GET /health` - Health check

### Screenplay Writer (:8080)
**Movie concept generation service**

- Generate original movie concepts using LLMs
- Fetch movie metadata from OMDb API
- Create detailed storylines and character descriptions
- See: [screenplay-writer/README.md](screenplay-writer/README.md)

**Endpoints:**
- `POST /generate-movie` - Generate movie concept
- `POST /fetch-movie-data` - Fetch movie data from OMDb
- `GET /health` - Health check

### Scene Decomposer (:8001)
**Trailer scene breakdown service**

- Break down movie concepts into trailer scenes
- Generate character designs and scene descriptions
- Optimize for visual storytelling
- See: [scene-decomposer/README.md](scene-decomposer/README.md)

**Endpoints:**
- `POST /generate-trailer` - Generate trailer breakdown
- `POST /analyze-movie` - Analyze movie structure
- `GET /health` - Health check

### Video Generator (:8003)
**AI-powered video generation**

- Generate character reference images using Gemini
- Create scene videos using Google VEO 3.1
- Stitch scenes into complete trailers
- Upload results to Google Cloud Storage

**Endpoints:**
- `POST /generate/character-references` - Generate character images
- `POST /generate/scene-videos` - Generate scene videos
- `POST /generate/trailer` - Full trailer generation
- `GET /health` - Health check

### Frontend (:3000)
**React-based user interface**

- Interactive quiz interface
- Real-time video player
- Results visualization
- GCS polling for generated videos
- See: [frontend/README.md](frontend/README.md)

### ChromaDB (:8000)
**Vector database for embeddings**

- Store and retrieve movie tag embeddings
- Similarity search for recommendations
- Persistent storage for taste vectors

## Pipeline Usage

### Orchestration Pipeline

The orchestration pipeline coordinates all microservices to generate complete trailers from taste vectors.

#### Simple Function Call

```python
from pipeline2 import generate_trailer

# Example taste vector (1100 dimensions)
taste_vector = [0.5, 0.3, 0.8, ...]

# Generate trailer
result = generate_trailer(
    taste_vector=taste_vector,
    custom_prompt="Create an epic sci-fi thriller",  # Optional
    output_name="my_awesome_trailer.mp4"  # Optional
)

# Check result
if result['success']:
    print(f"✅ Video available at: {result['gcs_url']}")
    print(f"⏱️  Took {result['execution_time']:.2f} seconds")
else:
    print(f"❌ Failed: {result['error']}")
```

#### Advanced OOP Approach

```python
from pipeline2 import TaraintinoOrchestrator

# Initialize orchestrator
orchestrator = TaraintinoOrchestrator(
    quiz_service_url="http://localhost:8082",
    screenplay_service_url="http://localhost:8080",
    scene_decomposer_url="http://localhost:8001",
    video_generator_url="http://localhost:8003",
    gcs_bucket_name="tarantaino-output",
    timeout=300
)

# Check service health
health = orchestrator.check_services_health()
print(health)

# Run full pipeline
result = orchestrator.generate_trailer_from_taste_vector(
    taste_vector=taste_vector
)

# Access intermediate results
print(f"Recommendations: {result['recommendations']}")
print(f"Movie Title: {result['movie_concept']['title']}")
print(f"Num Scenes: {len(result['trailer_breakdown']['scenes'])}")
```

#### Pipeline Flow

```
taste_vector → recommendations → movie concept → trailer breakdown → video generation → GCS upload
```

**Expected timing:**
- Step 1 (Movie Generation): ~10-20 seconds
- Step 2 (Trailer Breakdown): ~30-60 seconds
- Step 3 (Video Generation): 5-15 minutes
- Step 4 (GCS Upload): ~5-10 seconds

### Test the Pipeline

```bash
# Run simple test
python test_full_simple.py
```

Expected output:
```
🎬 SIMPLE FULL PIPELINE TEST
📝 Step 1/4: Generating movie concept...
✅ Generated: [Movie Title]
🎬 Step 2/4: Generating trailer breakdown...
✅ Generated 6 scenes with 4 characters
🎥 Step 3/4: Generating video...
✅ Video generated: [path]
☁️  Step 4/4: Uploading to GCS...
✅ Uploaded to: gs://tarantaino-output/trailers/trailer_[timestamp].mp4
🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!
```

## Integration Points

### Quiz Service → Pipeline

```python
# Quiz service outputs taste vector
taste_vector = quiz_service.get_taste_vector()

# Pipeline input
result = generate_trailer(taste_vector)
```

### Pipeline → Frontend

```python
# Pipeline stores video at:
gcs_url = "gs://tarantaino-output/trailers/trailer_<timestamp>.mp4"

# Frontend polls every 5 seconds:
# Check: frontend/app/generating/page.tsx
# When found, display video player
```

## Development Workflow

### Local Development

1. **Start services:**
   ```bash
   docker-compose up
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f <service-name>
   # Examples:
   docker-compose logs quiz-service
   docker-compose logs screenplay-writer
   docker-compose logs scene-decomposer
   docker-compose logs video-generator
   ```

3. **Rebuild service:**
   ```bash
   docker-compose up -d --build <service-name>
   ```

4. **Restart service:**
   ```bash
   docker-compose restart <service-name>
   ```

5. **Stop all services:**
   ```bash
   docker-compose down

   # Stop and remove volumes
   docker-compose down -v
   ```

### Component Development

**Docker/Infrastructure:**
```bash
# Modify docker-compose.yml
# Add services, adjust volumes, environment variables
docker-compose up --build
```

**Quiz Service:**
```bash
# Test quiz and taste vector generation
# Output: 1100-dimensional taste vector
# See: quiz-vector/README.md
```

**Orchestration Pipeline:**
```bash
# Test orchestration
python pipeline2.py
# Or:
from pipeline2 import generate_trailer
result = generate_trailer(taste_vector)
```

**Frontend:**
```bash
# Frontend polls GCS bucket every 5 seconds
# Check: frontend/app/generating/page.tsx
# Query: gs://tarantaino-output/trailers/trailer_*.mp4
```

## Environment Variables

All configuration is managed through environment variables. Copy `.env.example` to `.env` and configure:

**Key variables:**
- `OPENROUTER_API_KEY` - LLM service API key
- `OMDB_API_KEY` - Movie metadata API key
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key
- `GCS_BUCKET_NAME` - Google Cloud Storage bucket
- `CHROMA_SERVER_HOST` - ChromaDB host
- `DEFAULT_TRAILER_DURATION` - Target trailer length in seconds

**Important:** Never commit `.env` or service account keys to Git!

## Troubleshooting

### Services Won't Start

1. **Check logs:**
   ```bash
   docker-compose logs <service-name>
   ```

2. **Rebuild without cache:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Check port conflicts:**
   ```bash
   lsof -i :3000 :8000 :8001 :8003 :8080 :8082
   ```

### Service Health Check Fails

1. **Give services time to start** (30-60 seconds)
2. **Check API keys:**
   ```bash
   docker-compose exec screenplay-writer env | grep API_KEY
   ```
3. **Verify GCS credentials:**
   ```bash
   docker-compose exec video-generator ls -la /app/secret.json
   ```

### Pipeline Execution Errors

**Taste vector dimension mismatch:**
- Ensure taste vector has 1100 dimensions
- Match the number of tags in dataset

**Timeout errors:**
- Increase timeout in orchestrator (default: 300s)
- Video generation can take 5-15 minutes

**GCS upload fails:**
- Check `GOOGLE_APPLICATION_CREDENTIALS` path
- Verify service account has Storage Admin role
- Test manually:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
  python -c "from google.cloud import storage; print(storage.Client().project)"
  ```

**Scene-decomposer validation errors:**
- Check logs: `docker-compose logs scene-decomposer --tail=50`
- Common issues: invalid scene durations (must be 4-10 seconds)
- Rebuild: `docker-compose up -d --build scene-decomposer`

**Video generation 500 errors:**
- Verify `video-generator/secret.json` exists
- Check Gemini API key is valid
- Ensure VEO 3.1 is enabled: https://labs.google/veo
- Check logs: `docker logs video-generator --tail=50`

### Docker Build Failures

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t service-name .
```

## API Rate Limits

### OpenRouter
- Free tier: Varies by model
- Claude Haiku: Generally generous limits
- Monitor: https://openrouter.ai/activity

### Google Gemini
- Free tier: 60 requests per minute
- VEO video generation: Rate limited
- Monitor: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

## Configuration Files

```
AC215-TarAIntino-Big/
├── .env                              # Root environment (copy to services)
├── .env.example                      # Template
├── docker-compose.yml                # Service orchestration
├── pipeline2.py                      # Full orchestration pipeline
│
├── quiz-vector/
│   └── secrets/
│       └── llm-service-account.json  # GCS credentials
│
├── screenplay-writer/
│   └── .env                          # Service config
│
├── scene-decomposer/
│   └── .env                          # Service config
│
└── video-generator/
    └── secret.json                   # Gemini API credentials
```

## Resource Requirements

**Minimum:**
- RAM: 8GB
- Disk: 2GB for Docker images + 500MB per trailer
- Network: Stable internet for API calls

**Recommended:**
- RAM: 16GB
- Disk: 10GB
- Network: High-speed connection

## Updating Subtree Repositories

If you maintain separate repositories that are merged into this monorepo:

```bash
# Fetch changes from sub-repository
git fetch <repo_name>

# Pull changes into subtree
git subtree pull --prefix=<repo_name> <repo_name> main -m "chore: subtree pull <repo_name>"

# Push to main repository
git push origin main
```

## Best Practices

### Security
- Use environment variables for all secrets
- Never commit `.env` or credential files
- Store service account keys outside repository
- Use `.gitignore` for sensitive files

### Docker
- Health checks for monitoring
- Non-root users for security
- Volume mounts for persistent data
- Network isolation with Docker networks

### Testing
- Test each service independently
- Use health endpoints to verify status
- Monitor logs during development
- Test full pipeline before deployment

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Google Gemini API](https://ai.google.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenRouter API](https://openrouter.ai/docs)

### Service-Specific Documentation
- [Quiz Vector Service](quiz-vector/README.md)
- [Screenplay Writer Service](screenplay-writer/README.md)
- [Scene Decomposer Service](scene-decomposer/README.md)
- [Frontend Application](frontend/README.md)

## Support

For questions or issues:

1. Check the service-specific READMEs
2. Review the troubleshooting section
3. Check Docker logs for error messages
4. Verify all API keys and credentials
5. Contact the team maintainers

## Summary Checklist

Before running the full system:

- [ ] `.env` file configured with all API keys
- [ ] `video-generator/secret.json` created with Gemini API key
- [ ] Google Cloud service account key downloaded and path set
- [ ] GCS bucket created (`tarantaino-output`)
- [ ] All Docker services started (`docker-compose up -d`)
- [ ] All health endpoints responding (`/health`)
- [ ] Test script runs successfully (`python test_full_simple.py`)

**Estimated setup time:** 30-45 minutes (first time)

**Estimated first run time:** 15-20 minutes (including video generation)

---

**Happy Building!**
