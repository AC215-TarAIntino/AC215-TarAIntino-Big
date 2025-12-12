# AC215-TarAIntino-Big

**Team Members**

Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vrancic.

**Group Name**

TarAIntino

**Abstract**

TarAIntino is an end-to-end machine learning pipeline that creates personalized movie trailers based on user preferences. Indeed, in this project we aim to develop a comprehensive MLOps system for generating personalized movie trailers using taste vectors, LLMs, and video generation AI. The app will feature an adaptive quiz to elicit user preferences and include a modular pipeline connecting those preferences to generative APIs. Users can simply answer a short interactive quiz, and the app will produce a personalized, AI-generated movie trailer that reflects their cinematic taste. Additionally, a storytelling and trailer-planning agent will allow users to explore customized narratives and styles. It will be powered by a large language model for narrative generation and diffusion-based video models, making it a specialist in personalized cinematic creation.

**🌐 Live Application:** http://34.59.37.46/

## Overview

The system works as follows:
- **Analyzes user taste** through an interactive quiz interface
- **Generates movie concepts** using LLM-powered screenplay writing
- **Creates trailer breakdowns** with detailed scene descriptions
- **Produces video content** using Google Gemini/VEO 3.1
- **Delivers results** via a React-based frontend with real-time polling

**More detailed information is available in the `hand-ins/Application Design Document.pdf`.**

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

**More detailed architecture diagram available in `hand-ins/diagram/`.**

## Project Structure

```
AC215-TarAIntino-Big/
├── .github/
│   └── workflows/                  # CI/CD pipelines
│       ├── ci.yml                  # Main CI pipeline (all checks)
│       ├── backend-ci.yml          # Backend-specific CI
│       └── frontend-ci.yml         # Frontend-specific CI
├── .husky/
│   └── pre-commit                  # Git pre-commit hooks
├── hand-ins/                       # Project documentation & reports
│   ├── Application Design Document.pdf # Final Solution and Technical Architecture report
│   ├── TarAIntino Complete Run of App.mp4 # Demo video of the complete app running succesfully
│   ├── screenshots for CI CD/      # CI/CD status images + in Github Actions
│   ├── screenshots for test coverage # Test coverage results for all microservices
│   ├── diagram/                    # Architecture diagram
│   └── previous reports/           # Historical documentation and reports from previous milestones (project proposal, midterm ppt presentation, etc.)
├── tests/                          # Root-level integration tests
│   ├── test_end_to_end_trailer_generation.py
│   └── TEST_COVERAGE_SUMMARY.md
├── src/                            # All microservices
│   ├── deployment/                 # Infrastructure as Code (Pulumi)
│   │   ├── deploy_images/          # Docker image deployment to GCR
│   │   ├── deploy_k8s/             # Kubernetes cluster deployment
│   │   ├── deploy.sh               # Deployment automation script
│   │   └── setup-environment.sh    # Environment setup script
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
│   │   ├── pyproject.toml          # Service dependencies
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
│   │   ├── pyproject.toml          # Service dependencies
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
│   │   ├── pyproject.toml          # Service dependencies
│   │   ├── .env.example            # Environment template
│   │   ├── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   │   └── README.md               # Scene decomposer docs
│   ├── video-generator/            # Video generation service
│   │   ├── app.py                  # FastAPI application
│   │   ├── generate.py             # Video generation logic
│   │   ├── tests/                  # Unit tests
│   │   ├── output/                 # Generated videos
│   │   │   ├── refs/               # Character references
│   │   │   └── scenes/             # Generated scenes
│   │   ├── Dockerfile              # Container definition
│   │   ├── pyproject.toml          # Service dependencies
│   │   └── TEST_COVERAGE_SUMMARY.md # Test coverage report
│   └── frontend/                   # React frontend application
│       ├── app/                    # Next.js app directory
│       │   ├── api/                # API routes
│       │   ├── generating/         # Generation status page
│       │   └── result/             # Results page
│       ├── components/             # React components
│       │   ├── quiz/               # Quiz UI components
│       │   ├── result/             # Result display components
│       │   └── effects/            # Visual effects
│       ├── lib/                    # Utilities and services
│       │   ├── api/                # API clients
│       │   ├── data/               # Static data
│       │   └── utils/              # Helper functions
│       ├── public/                 # Static assets
│       ├── Dockerfile              # Container definition
│       ├── package.json            # Node dependencies
│       └── README.md               # Frontend documentation
├── Makefile                        # Development automation
├── docker-compose.yml              # Service orchestration
├── pyproject.toml                  # Python dependencies and config
├── watch.py                        # File watcher for auto-testing
├── setup-git-hooks.sh              # Git hooks installation script
├── monitor_pipeline.sh             # Pipeline monitoring utility
├── .env.example                    # Environment template
├── .dockerignore                   # Docker ignore rules
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Quick Start

### Prerequisites

- **Docker & Docker Compose** - For containerization
- **Python 3.11+** - For running pipelines and development tools
- **Node.js 20+** - For React frontend
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
./setup-git-hooks.sh  # Install pre-commit hooks (format + lint + test)
```

#### 2. Configure API Keys & Service Credentials

**Get your API keys:**
- **OpenRouter:** https://openrouter.ai/keys
- **OMDb:** http://www.omdbapi.com/apikey.aspx
- **Google Gemini:** https://aistudio.google.com/app/apikey
- **Google Cloud Service Account:** https://console.cloud.google.com/ → IAM & Admin → Service Accounts

Make sure your Github Actions secrets (Settings → Secrets and variables → Actions) are set up with the following:
  GCP_SA_KEY: <your GCP service account JSON>
  GCP_PROJECT_ID: <your-gcp-project-id>
  PULUMI_ACCESS_TOKEN: <your-pulumi-token>
  PULUMI_CONFIG_PASSPHRASE: <your-pulumi-stack-passphrase>

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
curl http://localhost:8080/health  # Screenplay Writer --> should return {"status":"healthy","omdb_configured":true,"openrouter_configured":true,"model":"anthropic/claude-3.5-sonnet"}
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

**An example of an entire run of the app is available in the hand-ins folder as "TarAIntino Complete Run of App.mp4".**

## Services

### Quiz Service (:8082)
**Interactive quiz and recommendation engine**

- Generate taste vectors from user preferences
- Retrieve movie recommendations using RAG
- Vector database integration with ChromaDB
- More detailed information in `src/quiz-vector/README.md`

### Screenplay Writer (:8080)
**Movie concept generation service**

- Generate original movie concepts using LLMs
- Fetch movie metadata from OMDb API
- Create detailed storylines and character descriptions
- More detailed information in `src/screenplay-writer/README.md`

### Scene Decomposer (:8001)
**Trailer scene breakdown service**

- Break down movie concepts into trailer scenes
- Generate character designs and scene descriptions
- Optimize for visual storytelling
- More detailed information in `src/scene-decomposer/README.md`

### Video Generator (:8003)
**AI-powered video generation**

- Generate character reference images using Gemini
- Create scene videos using Google VEO 3.1
- Stitch scenes into complete trailers
- Upload results to Google Cloud Storage
- More detailed information in `src/video-generator/README.md`

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

### Microservice Tests

Tests for all microservices using Docker for consistent testing environments.

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

**Results for all the microservices' tests can be found in their respective `TEST_COVERAGE_SUMMARY.md` files in each folder. Screenshots of the test coverage results are also available in the `hand-ins/screenshots for test coverage/` folder.**

### End-to-End Integration Tests

Comprehensive end-to-end tests covering the entire pipeline:

```bash
docker-compose up -d
docker run --rm --network host -v $(pwd)/tests:/tests taraintino-base:latest sh -c "pip install -q requests && python -m pytest /tests/test_end_to_end_trailer_generation.py -v"
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Push/PR                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       ci.yml (Main)                         │
│                    Runs on all changes                      │
└─────────────────────────────────────────────────────────────┘
        │                                           │
        ▼                                           ▼
┌──────────────────────┐              ┌──────────────────────┐
│   Frontend Checks    │              │   Backend Checks     │
├──────────────────────┤              ├──────────────────────┤
│ • TypeScript Check   │              │ • Black Format       │
│ • ESLint             │              │ • Ruff Lint          │
│ • Build              │              │ • Docker Compose     │
└──────────────────────┘              │ • Pytest (Docker)    │
                                      └──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Specialized Workflows (Optimized)              │
├─────────────────────────────────────────────────────────────┤
│  frontend-ci.yml          │       backend-ci.yml            │
│  (frontend changes only)  │       (Python changes only)     │
└─────────────────────────────────────────────────────────────┘
```

### Workflows

- **`ci.yml`** - Main CI pipeline that runs on all pushes and PRs
  - Runs frontend checks (TypeScript, ESLint, build)
  - Runs backend checks (black, ruff, docker-compose validation, pytest)
  - Comprehensive status check

- **`frontend-ci.yml`** - Specialized frontend pipeline
  - Triggers only on frontend file changes
  - TypeScript type-checking
  - ESLint linting
  - Build verification

- **`backend-ci.yml`** - Specialized backend pipeline
  - Triggers on Python, deployment, and docker-compose changes
  - Black formatting check
  - Ruff linting
  - Docker-compose syntax validation
  - Docker-based pytest for all microservices

**Deployment:** The CI/CD pipeline automatically deploys updates to the Kubernetes cluster upon merging changes into the main branch.

### CI Status

All pull requests must pass CI checks before merging. The CI pipeline automatically:
1. Formats code with black (check only)
2. Lints code with ruff (including deployment files)
3. Validates docker-compose.yml syntax
4. Runs all microservice tests in Docker containers
5. Verifies frontend build and type-safety

**Results of CI runs can be found in the `hand-ins/screenshots for CI CD/` folder.**

## Known Issues and Limitations

### System Limitations

- **Video Generation Time**: Full trailer generation takes 3-10 minutes due to Google VEO 3.1 processing
- **Cost**: Approximately $15-25 per 35-second trailer (Google Gemini/VEO pricing)
- **Session Storage**: Currently uses in-memory storage (not production-ready for large-scale deployment)
- **Dataset**: MovieLens Tag Genome dataset is static (2014 data, no real-time updates)
- **Concurrent Video Generation**: Limited by Google VEO API quotas and rate limits

### API Rate Limits

- **OMDb API**: 1,000 requests/day on free tier
- **OpenRouter**: Rate limits based on your subscription plan
- **Google Gemini/VEO**: Subject to Google Cloud quotas and daily limits
- **ChromaDB**: No built-in rate limiting (in-memory operations)

### Performance Notes

- **Cold Start Latency**: First quiz request may be slow (2-3 seconds) due to ChromaDB initialization
- **Scene Generation**: 30-120 seconds per scene (VEO 3.1 processing time)
- **Concurrent Users**: Limited by in-memory session storage (recommended: Redis for production)
- **ChromaDB Query Time**: Sub-second for vector similarity search (<500ms typical)

### Browser Compatibility

- **Minimum Requirements**: Modern browsers with HTML5 video support
  - Chrome 90+ (recommended)
  - Firefox 88+
  - Safari 14+
  - Edge 90+
- **Video Codec**: Requires WebM/MP4 codec support for trailer playback
- **JavaScript**: ES6+ features required (no IE11 support)

### Known Issues

- **Session Expiration**: Quiz sessions timeout after 30 minutes of inactivity (configurable)
- **Video Upload**: Large videos may timeout during GCS upload on slow connections

### Future Improvements

- Implement Redis for production-ready session management
- Add video generation queue/worker system for better scalability
- Implement user authentication and saved preference profiles
- Add real-time progress tracking for video generation
- Support multiple trailer lengths and aspect ratios
- Add music/soundtrack generation integration

## Development Tools

The project uses a comprehensive Makefile for development tasks. Run `make` or `make help` to see all available commands.

### Quick Commands

| Command | Description |
|---------|-------------|
| `make init` | Initialize project (check env, install deps, start services) |
| `make check` | Run format + lint + test (comprehensive check before commits) |
| `make up` | Start all Docker services |
| `make down` | Stop all Docker services |
| `make test` | Run all microservice tests |
| `make help` | Show all available commands |

### Code Quality

| Command | Description |
|---------|-------------|
| `make format` | Format code with black |
| `make format-check` | Check formatting without changes |
| `make lint` | Lint code with ruff (check only) |
| `make lint-fix` | Lint and auto-fix issues |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all microservice tests |
| `make test-cov` | Run tests with HTML coverage report |
| `make test-quiz` | Test quiz-vector only |
| `make test-screenplay` | Test screenplay-writer only |
| `make test-scene` | Test scene-decomposer only |
| `make test-video` | Test video-generator only |
| `make test-e2e` | End-to-end integration tests |

### Docker Management

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make ps` | Show running containers |
| `make logs` | Show logs from all services |
| `make logs-quiz` | Show quiz-service logs |
| `make clean-volumes` | Remove Docker volumes (deletes data!) |

### Automated Checks on File Changes

**Git Pre-Commit Hook (for teams)**

Automatically run checks before every commit to ensure code is always formatted and linted:

```bash
./setup-git-hooks.sh
```

### Development Workflow

```bash
# 1. Start development
make up                    # Start services
./setup-git-hooks.sh       # Install pre-commit hooks

# 2. Make changes, tests run automatically

# 3. Before committing
make check                 # Ensure everything passes

# 4. Commit (pre-commit hook runs if installed)
git add .
git commit -m "Your message"
```

## Happy Trailer Generating!


## Appendix - Final Project Submission Check
 
### ✅ CI/CD Pipeline

  - Workflow validation: All deployment configuration checks passed (12/12 checks)
  - YAML syntax: Valid
  - Deployment structure: All Pulumi files and directories are present
  - Job dependencies: Correctly configured

### ✅ Code Quality

  - Black formatting: All 58 files pass formatting checks
  - Ruff linting: All checks passed, no issues found
  - Code: Clean and properly formatted

### ✅ Docker & Services

  - docker-compose.yml: Syntax is valid
  - Services running: 8/8 services operational
  - Health checks: All backend services healthy
    - Quiz Service (8082): {"ok":true}
    - Screenplay Writer (8080): {"status":"healthy"}
    - Scene Decomposer (8001): {"status":"healthy"}
    - Video Generator (8003): {"status":"ok"}
    - Frontend (3000): Responding with HTTP 200

### ✅ Microservice Tests

  All tests passing with excellent coverage:

  | Service           | Tests Passed | Coverage |
  |-------------------|--------------|----------|
  | Quiz Service      | 132 tests    | 94.20%   |
  | Screenplay Writer | 73 tests     | 95.34%   |
  | Scene Decomposer  | 76 tests     | 97.29%   |
  | Video Generator   | 49 tests     | 94.55%   |
  | Total             | 330 tests    | ~95%     |

### ✅ Deployment Configuration

  - Pulumi Images (deploy_images/): ✓
    - __main__.py: Properly configured for Docker image builds
    - requirements.txt: All dependencies specified
    - Pulumi.yaml: Configuration valid
  - Pulumi Kubernetes (deploy_k8s/): ✓
    - __main__.py: Complete GKE deployment with:
        - Cluster creation with autoscaling (2-10 nodes)
      - All 5 microservices + ChromaDB
      - Persistent volumes for ChromaDB
      - LoadBalancer services
      - Horizontal Pod Autoscalers
      - Resource limits and health probes
    - requirements.txt: All dependencies specified
    - Pulumi.yaml: Configuration valid

### ✅ Frontend

  - Configuration files present and valid
  - TypeScript, ESLint configs in place
  - Running and responding successfully
  - CI/CD validates builds on every push