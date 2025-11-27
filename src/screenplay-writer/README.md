# Screenplay Writer Service

A FastAPI service that generates original movie concepts and detailed screenplays based on user preferences and movie recommendations.

## Overview

The Screenplay Writer takes movie recommendations from the Quiz Service and generates a completely original movie concept with:
- **Title**: Creative, engaging movie title
- **Logline**: One-sentence hook
- **Plot**: Full story synopsis (3-5 paragraphs)
- **Characters**: Detailed character descriptions with motivations
- **Themes**: Core themes and visual style
- **Genres**: Genre classifications

The service combines **OMDb API** (for inspiration from existing movies) with **OpenRouter LLM** (Gemini 3 Pro) for creative screenplay generation.

## Technology Stack

- **Framework**: FastAPI (Python)
- **LLM Provider**: OpenRouter (Google Gemini 3 Pro)
- **Movie Data**: OMDb API (Open Movie Database)
- **AI Model**: Google Gemini 3 Pro Preview
- **Port**: 8080

## Project Structure

```
screenplay-writer/
├── src/
│   └── movie_pipeline/         # Movie generation module
│       ├── api.py              # FastAPI endpoints
│       ├── config.py           # API configuration
│       ├── movie_fetcher.py    # OMDb API integration
│       ├── movie_generator.py  # LLM screenplay generation
│       └── schemas.py          # Request/response models
├── tests/                      # Unit tests
├── output/                     # Generated screenplays
├── .env.example                # Environment template
├── Dockerfile                  # Container definition
└── pyproject.toml              # Python dependencies
```

## How It Works

### 1. Movie Data Fetching (`movie_fetcher.py`)

**Purpose**: Gather inspiration from existing movies

**OMDb API provides**:
- Movie metadata (title, year, genre, plot)
- IMDB ratings and awards
- Cast and director information
- Similar movie suggestions

### 2. Screenplay Generation (`movie_generator.py`)

**Purpose**: Create original movie concepts using LLM

**Process**:
```
Movie Recommendations (from Quiz Service)
  ↓
Fetch metadata from OMDb API (for inspiration)
  ↓
Build creative prompt:
  - User's taste vector themes
  - Genre preferences
  - Similar successful movies
  - Unique storytelling elements
  ↓
Call Gemini 3 Pro via OpenRouter
  ↓
Generate original screenplay with:
  - Title
  - Logline
  - Full plot (3-5 paragraphs)
  - Character profiles
  - Visual themes
```

**LLM Prompt Strategy**:
- **Inspiration, not copying**: Uses recommended movies as thematic inspiration
- **Original creation**: Generates completely new stories, characters, plots
- **User alignment**: Matches user's taste preferences from quiz
- **Genre fusion**: Can blend multiple genres for unique concepts

## API Endpoints

### `POST /generate-movie`
Generate an original movie concept from recommendations.

### `POST /fetch-movie-data`
Fetch metadata from OMDb API for a specific movie.

### `GET /health`
Health check endpoint.

## Running Locally

-> See main [README](../README.md) for full setup instructions.

### Prerequisites

You need two API keys:

1. **OpenRouter API Key** - For LLM access
   - Sign up at [https://openrouter.ai/](https://openrouter.ai/)

2. **OMDb API Key** - For movie metadata
   - Get free key at [http://www.omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx)

## Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...
OMDB_API_KEY=...

# Optional (defaults shown)
OPENROUTER_MODEL=google/gemini-3-pro-preview
API_HOST=0.0.0.0
API_PORT=8000
```

## Configuration Options

- **`OPENROUTER_MODEL`**: LLM model for screenplay generation
  - Default: `google/gemini-3-pro-preview`
  - Options: Any OpenRouter-supported model

- **OMDb API**: Free tier allows 1,000 requests/day

## Data Flow

```
Movie Recommendations (from Quiz Service)
    ↓
Screenplay Writer API
    ↓
movie_fetcher.py
    → Call OMDb API
    → Get movie metadata
    ↓
movie_generator.py
    → Build creative prompt
    → Call Gemini 3 Pro via OpenRouter
    → Generate original screenplay
    ↓
Screenplay JSON
    ↓
Scene Decomposer Service
```

## Key Features

- **Original Content**: Generates unique stories, not remixes
- **User-Aligned**: Matches quiz-derived taste preferences
- **Genre Fusion**: Blends multiple genres intelligently
- **Character Depth**: Creates compelling, multi-dimensional characters
- **Visual Style**: Includes cinematography and aesthetic guidance
- **Fast Generation**: Typically 2-5 seconds per screenplay
- **Cost Effective**: Uses efficient Gemini 3 Pro model

## Notes

- **Originality**: All screenplays are AI-generated and original
- **Inspiration**: Recommended movies provide thematic inspiration only
- **Processing Time**: ~2-5 seconds for full screenplay generation
- **Cost**: Low cost with Gemini 3 Pro via OpenRouter
- **Output Length**: 500-1000 words typically
- **OMDb Limits**: 1,000 requests/day on free tier

## Related Documentation

- [Main Project README](../README.md)
- [System Architecture](../hand-ins/system-architecture-diagram.md)
- [Quiz Service Documentation](../quiz-vector/README.md)
- [Scene Decomposer Documentation](../scene-decomposer/README.md)
