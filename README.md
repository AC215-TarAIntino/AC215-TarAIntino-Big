# AC215-TarAIntino-Big

**Team Members**

Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vrancic

**Group Name**

TarAIntino

**Abstract**

TarAIntino is an end-to-end machine learning pipeline that creates personalized movie trailers based on user preferences. Indeed, in this project we aim to develop a comprehensive MLOps system for generating personalized movie trailers using taste vectors, LLMs, and video generation AI. The app will feature an adaptive quiz to elicit user preferences and include a modular pipeline connecting those preferences to generative APIs. Users can simply answer a short interactive quiz, and the app will produce a personalized, AI-generated movie trailer that reflects their cinematic taste. Additionally, a storytelling and trailer-planning agent will allow users to explore customized narratives and styles. It will be powered by a large language model for narrative generation and diffusion-based video models, making it a specialist in personalized cinematic creation.

## Overview

The system works as follows:
- **Analyzes user taste** through an interactive quiz interface
- **Generates movie concepts** using LLM-powered screenplay writing
- **Creates trailer breakdowns** with detailed scene descriptions
- **Produces video content** using Google Gemini/VEO 3.1
- **Delivers results** via a React-based frontend with real-time polling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   ChromaDB   │────▶│  Quiz RAG    │────▶│ Quiz Service│  │
│  │   :8000      │     │    App       │     │   :8082     │  │
│  └──────────────┘     └──────────────┘     └─────────────┘  │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │ Screenplay   │────▶│    Scene     │────▶│    Video    │  │
│  │   Writer     │     │  Decomposer  │     │  Generator  │  │
│  │   :8080      │     │   :8001      │     │   :8003     │  │
│  └──────────────┘     └──────────────┘     └─────────────┘  │
│  ┌──────────────┐                                           │
│  │   Frontend   │                                           │
│  │   :3000      │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
AC215-TarAIntino-Big/
├── .github/
│   └── workflows/                  # CI/CD pipelines
├── src/                            # All microservices
│   ├── quiz-vector/                # Quiz service and RAG system
│   │   ├── src/
│   │   │   ├── datapipeline/       # Data ingestion to ChromaDB
│   │   │   │   ├── downloader.py   # GCS to ChromaDB ingestion
│   │   │   │   └── uploader.py     # Upload data to GCS
│   │   │   └── quiz_service/       # Quiz API and preference model
│   │   │       ├── api.py          # FastAPI endpoints
│   │   │       ├── config.py       # Configuration
│   │   │       ├── model.py        # Bayesian taste model
│   │   │       ├── schemas.py      # Request/response schemas
│   │   │       ├── state.py        # Session management
│   │   │       └── utils.py        # Utility functions
│   │   ├── tests/                  # Unit tests
│   │   ├── secrets/                # GCS credentials
│   │   ├── Dockerfile              # Container definition
│   │   ├── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   │   └── README.md               # Quiz service documentation
│   ├── screenplay-writer/          # Movie concept generation
│   │   ├── src/
│   │   │   └── movie_pipeline/     # Screenplay generation module
│   │   │       ├── api.py          # FastAPI endpoints
│   │   │       ├── config.py       # Configuration
│   │   │       ├── movie_fetcher.py # OMDb API integration
│   │   │       ├── movie_generator.py # LLM screenplay writer
│   │   │       └── schemas.py      # Request/response schemas
│   │   ├── tests/                  # Unit tests
│   │   ├── output/                 # Generated screenplays
│   │   ├── Dockerfile              # Container definition
│   │   ├── .env.example            # Environment template
│   │   ├── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   │   └── README.md               # Screenplay service docs
│   ├── scene-decomposer/           # Trailer breakdown service
│   │   ├── src/
│   │   │   └── trailer_generator/  # Scene decomposition module
│   │   │       ├── api.py          # FastAPI endpoints
│   │   │       ├── config.py       # Configuration
│   │   │       ├── scene_analyzer.py # Screenplay analysis
│   │   │       ├── scene_generator.py # Scene breakdown logic
│   │   │       └── schemas.py      # Request/response schemas
│   │   ├── tests/                  # Unit tests
│   │   ├── outputs/                # Generated breakdowns
│   │   ├── Dockerfile              # Container definition
│   │   ├── .env.example            # Environment template
│   │   ├── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   │   └── README.md               # Scene decomposer docs
│   ├── video-generator/            # Video generation service
│   │   ├── app.py                  # FastAPI application
│   │   ├── generate.py             # Video generation logic
│   │   ├── test.py                 # Test utilities
│   │   ├── tests/                  # Unit tests
│   │   ├── output/                 # Generated videos
│   │   │   ├── refs/               # Character references
│   │   │   └── scenes/             # Generated scenes
│   │   ├── Dockerfile              # Container definition
│   │   ├── secrets.json            # Gemini API credentials
│   │   ├── gcp-credentials.json    # GCS credentials
│   │   └── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   └── frontend/                   # React frontend application
│       ├── app/                    # Next.js app directory
│       ├── components/             # React components
│       ├── public/                 # Static assets
│       └── README.md               # Frontend documentation
├── docker-compose.yml              # Service orchestration
├── pyproject.toml                  # Python dependencies and config
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Running the Project Locally

### Prerequisites

- **Docker & Docker Compose** - For containerization
- **Python 3.11+** - For running pipelines
- **Node.js 20+** - For React frontend (optional)
- **Google Cloud SDK** - For GCS deployment
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

#### 2. Configure API Keys & Service Credentials

**Get your API keys:**
- **OpenRouter:** https://openrouter.ai/keys
- **OMDb:** http://www.omdbapi.com/apikey.aspx
- **Google Gemini:** https://aistudio.google.com/app/apikey
- **Google Cloud Service Account:** https://console.cloud.google.com/ → IAM & Admin → Service Accounts

**Screenplay Writer Service:**
```bash
cd src/screenplay-writer
cp .env.example .env
# Edit .env and add your API keys:
# - OPENROUTER_API_KEY
# - OMDB_API_KEY
cd ../..
```

**Scene Decomposer Service:**
```bash
cd src/scene-decomposer
cp .env.example .env
# Edit .env and add your API keys:
# - OPENROUTER_API_KEY
cd ../..
```

**Quiz Vector Service:**
```bash
# Place service account key
cp /path/to/your-key.json src/quiz-vector/secrets/llm-service-account.json
```

**Video Generator Service:**
```bash
# Create Gemini API config
cat > src/video-generator/secret.json << 'EOF'
{
  "project_api_key": "YOUR_GEMINI_API_KEY_HERE"
}
EOF
```

### 3. Start All Services

```bash
# Build and start all services (in background)
docker-compose up --build -d

# Check service status
docker-compose ps -a

# Check logs of a specific service
docker-compose logs <service-name>

# To restart a specific service
docker-compose restart <service-name>

# Stop and remove volumes
docker-compose down -v
```

**Note:** On first startup, the `chroma-init` service will automatically populate ChromaDB with movie tag data from GCS. This process may take 1-2 minutes. The quiz service will wait for this initialization to complete before starting.

### 4. Verify Services

```bash
# Check health endpoints
curl http://localhost:8082/health  # Quiz Service --> should return {"ok":true}
curl http://localhost:8080/health  # Screenplay Writer --> should return {"status":"healthy","omdb_configured":true,"openrouter_configured":true,"model":"google/gemini-2.0-flash-exp:free"}
curl http://localhost:8001/health  # Scene Decomposer --> should return {"status":"healthy","openrouter_configured":true,"model":"anthropic/claude-3.5-sonnet","default_duration":35,"include_narration":true}
curl http://localhost:8003/health  # Video Generator --> should return {"status":"ok"}
```

### 5. Access Frontend, Run the App & Supervise Video Generation
First run
```bash
./monitor_pipeline.sh
```
to monitor the video generation process status in real-time.

Then launch the frontend in your browser at `http://localhost:3000` (opens Frontend service) and now you can start the quiz and generate your personalized movie trailer!

You will be able to see when the generation process is at in the terminal where you ran `monitor_pipeline.sh`.

## Services

### Quiz Service (:8082)
**Interactive quiz and recommendation engine**

- Generate taste vectors from user preferences
- Retrieve movie recommendations using RAG
- Vector database integration with ChromaDB
- More detailed information in `src/quiz-vector/README.md`

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
- More detailed information in `src/screenplay-writer/README.md`

**Endpoints:**
- `POST /generate-movie` - Generate movie concept
- `POST /fetch-movie-data` - Fetch movie data from OMDb
- `GET /health` - Health check

### Scene Decomposer (:8001)
**Trailer scene breakdown service**

- Break down movie concepts into trailer scenes
- Generate character designs and scene descriptions
- Optimize for visual storytelling
- More detailed information in `src/scene-decomposer/README.md`

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
- More detailed information in `src/video-generator/README.md`

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
- More detailed information in `src/frontend/README.md`

### ChromaDB (:8000)
**Vector database for embeddings**

- Store and retrieve movie tag embeddings
- Similarity search for recommendations
- Persistent storage for taste vectors
- **Automatic initialization**: Database is automatically populated from GCS on first startup via the `chroma-init` service

## Testing Pipeline

### Running Tests

All services use Docker for consistent testing environments.

First, ensure all services are running:
```bash
# CAREFUL: need to be in root folder here
docker-compose up --build -d
```

Then run tests for each service:
```bash
# Run all tests with coverage
docker-compose exec quiz-service python -m pytest tests/ --cov=. --cov-report=term-missing -v
docker-compose exec screenplay-writer python -m pytest tests/ --cov=. --cov-report=term-missing -v
docker-compose exec scene-decomposer python -m pytest tests/ --cov=. --cov-report=term-missing -v
docker-compose exec video-generator python -m pytest tests/ --cov=. --cov-report=term-missing -v
```

## Happy Trailer Generating!