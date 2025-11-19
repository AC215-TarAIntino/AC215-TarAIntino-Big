# TarAIntino - Full System Orchestration Guide

This guide explains how to run the complete TarAIntino system locally using Docker Compose and how to use the orchestration pipeline.

## 🎯 Quick Start

### 1. Prerequisites

- Docker & Docker Compose installed
- Google Cloud credentials (service account JSON)
- API Keys:
  - OpenRouter API key
  - OMDb API key

### 2. Setup Configuration

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and fill in your API keys:**
   ```bash
   OPENROUTER_API_KEY=your_key_here
   OMDB_API_KEY=your_key_here
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

3. **Place service account credentials:**
   - For quiz-vector: `quiz-vector/secrets/llm-service-account.json`
   - For Video_Generator: `Video_Generator/secrets.json`

4. **Copy .env to service directories:**
   ```bash
   cp .env screenplay-writer/.env
   cp .env scene-decomposer/.env
   ```

### 3. Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 4. Verify Services Are Running

```bash
# Check service health
curl http://localhost:8082/health  # Quiz Service
curl http://localhost:8080/health  # Screenplay Writer
curl http://localhost:8001/health  # Scene Decomposer
curl http://localhost:8003/health  # Video Generator
curl http://localhost:3000         # Frontend
```

## 📦 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: tarantino-network         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │   ChromaDB   │────▶│  Quiz RAG    │────▶│ Quiz Service│ │
│  │   :8000      │     │    App       │     │   :8082     │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ Screenplay   │     │    Scene     │     │    Video    │ │
│  │   Writer     │     │  Decomposer  │     │  Generator  │ │
│  │   :8080      │     │   :8001      │     │   :8003     │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│                                                               │
│  ┌──────────────┐                                            │
│  │   Frontend   │                                            │
│  │   :3000      │                                            │
│  └──────────────┘                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Using the Orchestration Pipeline

### Team Responsibilities

#### Karlo (pipeline1.py)
- Simulates quiz interaction
- Outputs: **taste vector** (1100-dimensional array)

#### Robby (pipeline2.py)
- Takes taste vector as input
- Orchestrates all microservices
- Outputs: **final video in GCS bucket**

### Example Usage

```python
# In pipeline2.py or your script
from pipeline2 import generate_trailer

# Example taste vector from Karlo's pipeline1.py
taste_vector = [0.5, 0.3, 0.8, ...]  # 1100 dimensions

# Generate trailer with simple function call
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

### Advanced Usage (OOP Approach)

```python
from pipeline2 import TaraintinoOrchestrator

# Initialize orchestrator with custom settings
orchestrator = TaraintinoOrchestrator(
    quiz_service_url="http://localhost:8082",
    screenplay_service_url="http://localhost:8080",
    scene_decomposer_url="http://localhost:8001",
    video_generator_url="http://localhost:8003",
    gcs_bucket_name="tarantaino-output",
    timeout=300
)

# Check all services are healthy
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

## 🔧 Service Endpoints

### Quiz Service (:8082)
- `POST /quiz/start` - Start new quiz session
- `POST /quiz/answer` - Submit answer
- `POST /recommend` - Get recommendations from taste vector
- `GET /health` - Health check

### Screenplay Writer (:8080)
- `POST /generate-movie` - Generate movie concept
- `POST /fetch-movie-data` - Fetch movie data from OMDb
- `GET /health` - Health check

### Scene Decomposer (:8001)
- `POST /generate-trailer` - Generate trailer breakdown
- `POST /analyze-movie` - Analyze movie
- `GET /health` - Health check

### Video Generator (:8003)
- `POST /generate/character-references` - Generate character images
- `POST /generate/scene-videos` - Generate scene videos
- `POST /generate/trailer` - Full trailer generation
- `GET /health` - Health check

### Frontend (:3000)
- Interactive quiz UI
- Video player
- Results visualization

## 🐛 Troubleshooting

### Services won't start

1. **Check logs:**
   ```bash
   docker-compose logs <service-name>
   # Examples:
   docker-compose logs quiz-service
   docker-compose logs video-generator
   ```

2. **Rebuild without cache:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Check port conflicts:**
   ```bash
   # Make sure no other services are using these ports
   lsof -i :3000 :8000 :8001 :8003 :8080 :8082
   ```

### Service health check fails

1. **Give services time to start:**
   - Some services take 30-60 seconds to fully initialize
   - Wait for "Uvicorn running on..." messages in logs

2. **Check API keys are set:**
   ```bash
   docker-compose exec screenplay-writer env | grep API_KEY
   ```

3. **Verify GCS credentials:**
   ```bash
   docker-compose exec video-generator ls -la /app/secrets.json
   ```

### Pipeline execution errors

1. **Taste vector dimension mismatch:**
   - Ensure taste vector has 1100 dimensions
   - Match the number of tags in the dataset

2. **Timeout errors:**
   - Increase timeout in orchestrator initialization
   - Video generation can take 5-10 minutes

3. **GCS upload fails:**
   - Check GOOGLE_APPLICATION_CREDENTIALS is set correctly
   - Verify service account has write permissions to bucket

## 📊 Development Workflow

### For Mathilde (Docker/Infrastructure)
```bash
# Modify docker-compose.yml
# Add new services, adjust volumes, environment variables, etc.
docker-compose up --build
```

### For Karlo (pipeline1.py)
```bash
# Test quiz simulation locally
python pipeline1.py

# Output should be a taste vector that can be passed to pipeline2
```

### For Robby (pipeline2.py)
```bash
# Test orchestration locally
python pipeline2.py

# Or in Python:
from pipeline2 import generate_trailer
result = generate_trailer(taste_vector)
```

### For Maddy (Frontend polling)
```bash
# Frontend polls GCS bucket every 5 seconds
# Check: frontend/app/generating/page.tsx
# Should query: gs://tarantaino-output/trailers/trailer_*.mp4
```

## 🔄 Integration Points

### Karlo → Robby
```python
# Karlo's output (pipeline1.py)
taste_vector = quiz_simulation.get_taste_vector()

# Robby's input (pipeline2.py)
result = generate_trailer(taste_vector)
```

### Robby → Maddy
```python
# Robby stores video at:
gcs_url = "gs://tarantaino-output/trailers/trailer_<timestamp>.mp4"

# Maddy's frontend polls:
# Every 5 seconds, check if file exists
# When found, display video player
```

## 📝 Configuration Files Location

```
AC215-TarAIntino-Big/
├── .env                              # Root environment (copy to services)
├── .env.example                      # Template
├── docker-compose.yml                # Main orchestration file
├── pipeline1.py                      # Karlo's quiz simulation
├── pipeline2.py                      # Robby's orchestration
│
├── quiz-vector/
│   └── secrets/
│       └── llm-service-account.json  # GCS credentials
│
├── screenplay-writer/
│   └── .env                          # Service-specific config
│
├── scene-decomposer/
│   └── .env                          # Service-specific config
│
└── Video_Generator/
    └── secrets.json                  # GCS credentials
```

## 🎬 Next Steps

1. **Mathilde**: Enhance docker-compose.yml with additional configs
2. **Karlo**: Implement pipeline1.py and integrate with frontend
3. **Robby**: Test pipeline2.py end-to-end with real taste vectors
4. **Maddy**: Implement GCS polling in frontend (every 5 seconds)

## 🆘 Need Help?

- Check service logs: `docker-compose logs -f <service>`
- Restart specific service: `docker-compose restart <service>`
- Full reset: `docker-compose down -v && docker-compose up --build`
- Check network: `docker network inspect tarantino-network`

---

**Happy Orchestrating! 🎬🍿**
