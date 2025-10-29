# Movie Pipeline

A movie inspiration pipeline that generates new movie concepts based on existing movies. Uses OMDb API for movie data and OpenRouter for LLM-powered generation.

## Overview

This module fetches detailed information about existing movies and uses an LLM to generate a completely new movie concept that would appeal to fans of those films. Perfect for:

- Creative brainstorming for screenwriters
- Market research for production companies
- Educational projects about film analysis
- Part of larger film-related systems

## Features

- **Movie Data Fetching**: Retrieves comprehensive movie information from OMDb (plot, cast, ratings, etc.)
- **LLM Generation**: Uses OpenRouter to generate detailed, creative movie concepts
- **Multiple Interfaces**: Use as REST API, Python library, or CLI tool
- **Flexible Model Selection**: Support for various LLM models via OpenRouter
- **Docker Ready**: Easy containerization and deployment
- **Comprehensive Output**: Generates detailed movie specs including plot, cast, budget, themes, and more

## Architecture

```
Input: Movie Names → OMDb API → Data Aggregation → OpenRouter LLM → Generated Movie JSON
```

## Prerequisites

- Python 3.10 or higher
- OMDb API key (free from [omdbapi.com](https://www.omdbapi.com/apikey.aspx))
- OpenRouter API key (from [openrouter.ai](https://openrouter.ai/keys))

## Installation

### Option 1: Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd mcp-screenplay
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Option 2: Docker

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

## Configuration

Create a `.env` file with the following variables:

```bash
# Required
OMDB_API_KEY=your_omdb_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional - Model Selection
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Available Models

**Free Models** (via OpenRouter):
- `google/gemini-2.0-flash-exp:free` (default)
- `meta-llama/llama-3.2-3b-instruct:free`

**Paid Models** (examples):
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `google/gemini-pro-1.5`

## Usage

### 1. REST API

**Start the server:**
```bash
# Local
python -m uvicorn src.movie_pipeline.api:app --reload

# Or with the built-in runner
python src/movie_pipeline/api.py
```

**Generate a movie:**
```bash
curl -X POST http://localhost:8000/generate-movie \
  -H "Content-Type: application/json" \
  -d '{
    "movie_names": ["Inception", "The Matrix", "Interstellar"]
  }'
```

**Fetch movie data only:**
```bash
curl -X POST http://localhost:8000/fetch-movie-data \
  -H "Content-Type: application/json" \
  -d '["Inception", "The Matrix"]'
```

**Health check:**
```bash
curl http://localhost:8000/health
```

### 2. Standalone CLI Tool

```bash
python tests/test_standalone.py --movies "Inception,The Matrix,Interstellar"
```

**Options:**
- `--movies`: Comma-separated list of movie names (required)
- `--model`: Override default OpenRouter model
- `--output`: Output JSON file path (default: generated_movie.json)
- `--no-save`: Don't save to file, only display

**Example:**
```bash
python tests/test_standalone.py \
  --movies "Blade Runner,Ghost in the Shell,Ex Machina" \
  --model "anthropic/claude-3.5-sonnet" \
  --output my_movie.json
```

### 3. Python Library

```python
from src.movie_pipeline import MovieFetcher, MovieGenerator

# Fetch movie data
fetcher = MovieFetcher()
movies = fetcher.fetch_multiple_movies(["Inception", "The Matrix"])

# Generate new movie
generator = MovieGenerator()
generated_movie = generator.generate_from_movies(movies)

# Access the generated data
print(f"Title: {generated_movie.title}")
print(f"Plot: {generated_movie.plot_summary}")
print(f"Cast: {[f'{c.actor} as {c.role}' for c in generated_movie.cast]}")

# Export to JSON
import json
with open('output.json', 'w') as f:
    json.dump(generated_movie.model_dump(), f, indent=2)
```

## API Reference

### POST /generate-movie

Generate a new movie concept based on existing movies.

**Request Body:**
```json
{
  "movie_names": ["Movie 1", "Movie 2", "Movie 3"],
  "model": "google/gemini-2.0-flash-exp:free"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "movie": {
    "title": "Generated Movie Title",
    "tagline": "Catchy tagline",
    "genres": ["Sci-Fi", "Thriller"],
    "plot_summary": "Detailed plot...",
    "director": "Director Name",
    "writers": ["Writer 1", "Writer 2"],
    "cast": [
      {"actor": "Actor Name", "role": "Character Name"}
    ],
    "runtime": "142 min",
    "rating": "PG-13",
    "release_year": 2026,
    "production_company": "Studio Name",
    "budget": "$150M",
    "themes": ["Theme1", "Theme2"],
    "visual_style": "Description...",
    "target_audience": "Description...",
    "unique_selling_point": "What makes it special...",
    "similar_movies": ["Similar Movie 1"],
    "inspiration_source": ["Movie 1", "Movie 2"]
  },
  "input_movies_found": 3,
  "model_used": "google/gemini-2.0-flash-exp:free"
}
```

## Project Structure

```
mcp-screenplay/
├── src/
│   └── movie_pipeline/
│       ├── __init__.py           # Package initialization
│       ├── config.py              # Configuration management
│       ├── movie_fetcher.py       # OMDb API client
│       ├── movie_generator.py     # OpenRouter LLM integration
│       ├── schemas.py             # Pydantic models
│       └── api.py                 # FastAPI application
├── tests/
│   └── test_standalone.py         # CLI testing script
├── docs/                          # Documentation
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker container config
├── docker-compose.yml             # Docker Compose config
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## Development

### Running Tests

```bash
# Test with sample movies
python tests/test_standalone.py --movies "The Godfather,Goodfellas,Casino"

# Test API endpoint
curl -X POST http://localhost:8000/generate-movie \
  -H "Content-Type: application/json" \
  -d '{"movie_names": ["Pulp Fiction", "Reservoir Dogs"]}'
```

### Adding to Larger Systems

This module is designed to be integrated into larger systems:

```python
# Import and use in your application
from src.movie_pipeline import MovieFetcher, MovieGenerator

class YourLargerSystem:
    def __init__(self):
        self.movie_fetcher = MovieFetcher()
        self.movie_generator = MovieGenerator()

    def generate_inspired_movie(self, movie_names):
        movies = self.movie_fetcher.fetch_multiple_movies(movie_names)
        return self.movie_generator.generate_from_movies(movies)
```

## Limitations & Considerations

- **OMDb API**: Free tier limited to 1,000 requests/day
- **OpenRouter**: Costs vary by model (free options available)
- **Rate Limits**: Be mindful of API rate limits in production
- **Movie Matching**: Movie titles must match OMDb database entries
- **LLM Output**: Quality depends on the selected model

## Future Enhancements

- [ ] Add caching layer to reduce API calls
- [ ] Support for TV shows in addition to movies
- [ ] Batch processing for multiple generations
- [ ] Alternative movie data sources (TMDB, etc.)
- [ ] MCP server integration option
- [ ] Fine-tuning prompts for different genres
- [ ] Movie poster generation integration

## Troubleshooting

### "Movie not found" errors
- Verify the movie title matches the OMDb database
- Try including the year: `fetch_movie_by_title("Inception", year="2010")`

### API Key errors
- Check that your `.env` file is in the project root
- Verify API keys are valid and not expired
- Ensure environment variables are loaded correctly

### Docker issues
- Make sure ports aren't already in use
- Check Docker logs: `docker-compose logs -f`
- Rebuild if needed: `docker-compose up --build`

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on the repository.
