# Scene Decomposer Service

A FastAPI service that analyzes movie screenplays and generates detailed scene-by-scene breakdowns optimized for AI video generation.

## Overview

The Scene Decomposer takes a full movie screenplay and breaks it down into 6-8 trailer scenes (35 seconds total by default). Each scene includes detailed visual descriptions, character appearances, camera angles, and narration - perfectly formatted for video generation models like Google VEO 3.1.

## Technology Stack

- **Framework**: FastAPI (Python)
- **LLM Provider**: OpenRouter (Google Gemini 3 Pro)
- **AI Model**: Google Gemini 3 Pro Preview (for scene analysis)
- **Port**: 8001

## Project Structure

```
scene-decomposer/
├── src/
│   └── trailer_generator/      # Scene decomposition module
│       ├── api.py              # FastAPI endpoints
│       ├── config.py           # OpenRouter configuration
│       ├── scene_analyzer.py   # Screenplay structure analysis
│       ├── scene_generator.py  # Scene breakdown generation
│       └── schemas.py          # Request/response models
├── tests/                      # Unit tests
├── outputs/                    # Generated scene breakdowns
├── .env.example                # Environment template
├── Dockerfile                  # Container definition
└── pyproject.toml              # Python dependencies
```

## How It Works

### 1. Screenplay Analysis (`scene_analyzer.py`)

**Purpose**: Understand the narrative structure of the screenplay

**Process**:
```
Screenplay JSON
  → Extract key elements:
    - Plot structure (3-act breakdown)
    - Main characters
    - Key plot points
    - Emotional beats
    - Visual themes
```

### 2. Scene Generation (`scene_generator.py`)

**Purpose**: Break down screenplay into trailer-ready scenes

**Gemini 3 Pro analyzes**:
- **Opening Hook**: Grab attention in first 3-5 seconds
- **Character Introductions**: Show protagonists and relationships
- **Rising Action**: Build tension and conflict
- **Climax Tease**: Hint at the peak without spoilers
- **Visual Variety**: Mix wide shots, close-ups, action sequences

**Output**: 6-8 scenes with:
- **Scene Number**: Sequential ordering
- **Duration**: Time allocation (3-8 seconds per scene)
- **Description**: Detailed visual description for video generation
- **Characters**: Who appears in this scene
- **Visual Style**: Cinematography, lighting, mood
- **Camera Movement**: Static, pan, zoom, tracking shot, etc.
- **Narration**: Optional voice-over or dialogue snippet

## API Endpoints

### `POST /generate-trailer`
Generate a complete trailer breakdown from a screenplay.

### `POST /analyze-movie`
Analyze screenplay structure without generating scenes.

### `GET /health`
Health check endpoint.

## Running Locally

-> See main [README](../README.md) for full setup instructions.

### Prerequisites

You need an **OpenRouter API key** to use this service.

1. Sign up at [https://openrouter.ai/](https://openrouter.ai/)
2. Create an API key
3. Add to `.env` file:

```bash
cp .env.example .env
# Edit .env and add:
OPENROUTER_API_KEY=sk-or-v1-...
```

## Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional (defaults shown)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
TRAILER_DURATION=35
NUM_SCENES=7
INCLUDE_NARRATION=true
API_HOST=0.0.0.0
API_PORT=8001
```

## Configuration Options

The service can be configured via environment variables in `.env`:

- **`OPENROUTER_MODEL`**: LLM model to use (default: `anthropic/claude-3.5-sonnet`)
- **`TRAILER_DURATION`**: Total trailer length in seconds (default: 35)
- **`NUM_SCENES`**: Number of scenes to generate (default: 7)
- **`INCLUDE_NARRATION`**: Add voice-over narration (default: true)

## Data Flow

```
Screenplay (from Screenplay Writer)
    ↓
Scene Decomposer API
    ↓
scene_analyzer.py
    → Analyze plot structure
    → Identify key moments
    → Extract themes
    ↓
scene_generator.py
    → Call Gemini 3 Pro via OpenRouter
    → Generate 6-8 scenes
    → Optimize for video generation
    ↓
Scene Breakdown JSON
    ↓
Video Generator Service
```

## Key Features

- **Intelligent Scene Selection**: Chooses the most visually compelling moments
- **Pacing Optimization**: Balances scene durations for trailer rhythm
- **Character Continuity**: Tracks character appearances across scenes
- **Visual Variety**: Ensures diverse camera angles and compositions
- **Narration Generation**: Creates compelling voice-over when enabled
- **Flexible Duration**: Adjustable trailer length (20-60 seconds)

## Notes

- **Scene Count**: 6-8 scenes works best for 30-40 second trailers
- **Processing Time**: ~5-15 seconds depending on screenplay length
- **Cost**: ~$0.02-0.05 per trailer (Gemini 3 Pro pricing)
- **Output Format**: JSON optimized for VEO 3.1 video generation
- **Scene Duration**: Individual scenes range from 3-8 seconds

## Related Documentation

- [Main Project README](../README.md)
- [System Architecture](../hand-ins/system-architecture-diagram.md)
- [Screenplay Writer Documentation](../screenplay-writer/README.md)
- [Video Generator Documentation](../video-generator/README.md)