# Trailer Generator API

AI-powered microservice that generates detailed scene-by-scene trailer breakdowns from movie descriptions. Creates production-ready prompts for video generation (VEO 3.1), image generation (DALL-E/Flux), and narration (ElevenLabs).

## Overview

This service takes a complete movie description (from `mcp-screenplay` or similar) and generates a detailed trailer breakdown with:

- **Scene-by-scene structure**: 4-8 scenes, each 4-8 seconds long
- **Image generation prompts**: Detailed start/end frame descriptions
- **Video generation prompts**: Comprehensive VEO 3.1 prompts with motion, camera movement, cinematography
- **Character consistency**: Ensures characters appear in continuous scenes for VEO 3.1 consistency
- **Optional narration**: Script for ElevenLabs voice generation
- **Technical specifications**: Color grading, aspect ratio, sound design notes

## Key Features

- **Character Consistency Management**: Intelligent scene structuring to maintain character appearance consistency across trailer
- **Detailed Prompts**: 5-7 sentence video prompts with explicit motion, camera movement, and cinematography instructions
- **Continuity Tracking**: End frame of scene N becomes start frame of scene N+1
- **Flexible Duration**: Generate 20-60 second trailers
- **Multiple Interfaces**: REST API, Python library, or standalone CLI
- **Docker Ready**: Easy containerization and deployment

## Architecture

Part of a larger AI movie production pipeline:

```
mcp-screenplay → movie.json
    ↓
mcp-trailer-generator → trailer_scenes.json
    ↓
orchestrator-service → actual video (VEO 3.1 API calls)
```

**Design Philosophy**: This service handles creative decisions (what scenes, what prompts). Actual API calls to VEO, DALL-E, and ElevenLabs are handled by a separate orchestration service for:
- Cost-effective testing
- Provider flexibility
- Replay capability
- Version control

## Prerequisites

- Python 3.10 or higher
- OpenRouter API key (from [openrouter.ai](https://openrouter.ai/keys))

## Installation

### Option 1: Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd mcp-trailer-generator
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
# Edit .env and add your OpenRouter API key
```

### Option 2: Docker

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API key
```

2. **Build and run**
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8001`

## Configuration

Create a `.env` file with:

```bash
# Required
OPENROUTER_API_KEY=your_api_key_here

# Optional - Model Selection
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=8001

# Optional - Generation Defaults
DEFAULT_TRAILER_DURATION=35
INCLUDE_NARRATION=true
```

## Usage

### 1. REST API

**Start the server:**
```bash
# Local
python -m uvicorn src.trailer_generator.api:app --reload

# Or with the built-in runner
python src/trailer_generator/api.py
```

**Generate a trailer:**
```bash
curl -X POST http://localhost:8001/generate-trailer \
  -H "Content-Type: application/json" \
  -d @path/to/movie.json
```

**With custom parameters:**
```bash
curl -X POST http://localhost:8001/generate-trailer \
  -H "Content-Type: application/json" \
  -d '{
    "movie": { ...movie data... },
    "target_duration": 45,
    "include_narration": true,
    "model": "anthropic/claude-3.5-sonnet"
  }'
```

**Analyze a movie (preview):**
```bash
curl -X POST http://localhost:8001/analyze-movie \
  -H "Content-Type: application/json" \
  -d @path/to/movie.json
```

**Health check:**
```bash
curl http://localhost:8001/health
```

### 2. Standalone CLI Tool

```bash
python tests/test_standalone.py \
  --movie-file path/to/movie.json
```

**Options:**
- `--movie-file`: Path to movie JSON file (required)
- `--duration`: Trailer duration in seconds (20-60, default: 35)
- `--no-narration`: Disable narration script
- `--model`: Override default OpenRouter model
- `--output`: Output JSON file path (default: outputs/trailer_breakdown.json)
- `--no-save`: Don't save to file, only display

**Example:**
```bash
python tests/test_standalone.py \
  --movie-file ../mcp-screenplay/outputs/test_scifi.json \
  --duration 45 \
  --output outputs/scifi_trailer.json
```

### 3. Python Library

```python
from trailer_generator.schemas import GeneratedMovie, TrailerRequest
from trailer_generator.scene_generator import SceneGenerator

# Load movie data
import json
with open('movie.json', 'r') as f:
    movie_data = json.load(f)
movie = GeneratedMovie(**movie_data)

# Generate trailer
generator = SceneGenerator()
trailer = generator.generate_trailer(
    movie=movie,
    target_duration=35,
    include_narration=True
)

# Access the scenes
for scene in trailer.scenes:
    print(f"Scene {scene.scene_number}: {scene.scene_type}")
    print(f"Duration: {scene.duration_seconds}s")
    print(f"Video Prompt: {scene.video_prompt}")
```

## API Reference

### POST /generate-trailer

Generate a complete trailer scene breakdown.

**Request Body:**
```json
{
  "movie": {
    "title": "Movie Title",
    "tagline": "...",
    "genres": ["Sci-Fi", "Thriller"],
    "plot_summary": "...",
    "cast": [...],
    "visual_style": "...",
    ...
  },
  "target_duration": 35,
  "include_narration": true,
  "model": "anthropic/claude-3.5-sonnet"
}
```

**Response:**
```json
{
  "success": true,
  "trailer": {
    "movie_title": "Movie Title",
    "total_duration": 35,
    "scenes": [
      {
        "scene_number": 1,
        "duration_seconds": 6,
        "scene_type": "establishing",
        "start_frame_prompt": "Detailed 4-5 sentence description...",
        "end_frame_prompt": "Detailed 4-5 sentence description...",
        "video_prompt": "Detailed 5-7 sentence prompt with explicit camera movement...",
        "characters_present": ["Character Name"],
        "audio_notes": "Sound design description...",
        "continuity_note": "Optional note"
      }
    ],
    "narration_script": "Compelling narration text...",
    "continuity_guide": "Character consistency guide...",
    "technical_specs": {
      "color_grading": "Desaturated with teal shadows...",
      "aspect_ratio": "2.39:1",
      "visual_style": "...",
      "sound_design_notes": "..."
    },
    "character_appearance_map": {
      "Character Name": [1, 3, 5]
    }
  },
  "model_used": "anthropic/claude-3.5-sonnet",
  "generation_time_seconds": 12.5
}
```

### POST /analyze-movie

Analyze a movie to extract key information.

**Request Body:** Complete `GeneratedMovie` JSON

**Response:**
```json
{
  "main_characters": [
    {
      "name": "Character Name",
      "actor": "Actor Name",
      "physical_description": "...",
      "role": "...",
      "traits": "..."
    }
  ],
  "key_themes": ["Theme1", "Theme2"],
  "visual_style_summary": "...",
  "tone": "tense and suspenseful",
  "hook_elements": ["Hook1", "Hook2"]
}
```

## Understanding the Output

### Scene Structure

Each scene includes three critical prompts:

1. **start_frame_prompt**: Detailed description for generating the opening image
   - Character physical descriptions
   - Lighting and color palette
   - Composition and camera angle
   - Setting details

2. **end_frame_prompt**: Detailed description for the closing image
   - Shows progression from start frame
   - Will become the next scene's start frame
   - Maintains visual consistency

3. **video_prompt**: Comprehensive instructions for VEO 3.1
   - Explicit camera movement (dolly, crane, handheld, etc.)
   - Subject motion description
   - Pacing and timing
   - Cinematography style
   - Specific events that occur
   - Atmosphere and mood

### Character Consistency

The system ensures characters appear in **continuous scenes** to maintain consistency:

```
❌ BAD: Character A in Scene 1, Character B in Scene 2, Character A again in Scene 3
✅ GOOD: Character A in Scene 1 (8s continuous), Character B in Scene 2, ...
```

This is crucial because VEO 3.1 maintains consistency by chaining end_frame → start_frame.

## Integration with Larger Systems

### Recommended Architecture

```
┌─────────────────┐
│ mcp-screenplay  │ → Generates movie descriptions
└────────┬────────┘
         │
         ↓ movie.json
┌─────────────────────┐
│ mcp-trailer-        │ → Generates scene breakdown
│ generator           │
└────────┬────────────┘
         │
         ↓ trailer_scenes.json
┌─────────────────────┐
│ Orchestrator        │ → Calls VEO, DALL-E, ElevenLabs APIs
│ Service             │ → Stitches video
└────────┬────────────┘
         │
         ↓
    final_trailer.mp4
```

### Example Integration

```python
# In your orchestrator service
import requests

# 1. Generate movie description
movie_response = requests.post(
    "http://mcp-screenplay:8000/generate-movie",
    json={"movie_names": ["Inception", "The Matrix"]}
)
movie = movie_response.json()["movie"]

# 2. Generate trailer breakdown
trailer_response = requests.post(
    "http://mcp-trailer-generator:8001/generate-trailer",
    json={"movie": movie, "target_duration": 35}
)
trailer = trailer_response.json()["trailer"]

# 3. Generate actual video (your orchestrator logic)
for scene in trailer["scenes"]:
    # Generate start/end frames with DALL-E
    start_img = generate_image(scene["start_frame_prompt"])
    end_img = generate_image(scene["end_frame_prompt"])

    # Generate video with VEO 3.1
    video = generate_video(
        prompt=scene["video_prompt"],
        start_frame=start_img,
        end_frame=end_img,
        duration=scene["duration_seconds"]
    )

    # Collect videos...
```

## Project Structure

```
mcp-trailer-generator/
├── src/
│   └── trailer_generator/
│       ├── __init__.py           # Package initialization
│       ├── config.py              # Configuration management
│       ├── schemas.py             # Pydantic models
│       ├── scene_analyzer.py     # Movie analysis logic
│       ├── scene_generator.py    # LLM-based scene generation
│       └── api.py                 # FastAPI application
├── tests/
│   └── test_standalone.py         # CLI testing script
├── outputs/                       # Generated trailer JSONs
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
# Test with a movie file
python tests/test_standalone.py \
  --movie-file path/to/movie.json

# Test API endpoint
curl -X POST http://localhost:8001/generate-trailer \
  -H "Content-Type: application/json" \
  -d @movie.json
```

### Environment Variables

All configuration via environment variables or `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `OPENROUTER_MODEL` | Model to use | `anthropic/claude-3.5-sonnet` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8001` |
| `DEFAULT_TRAILER_DURATION` | Default duration | `35` |
| `INCLUDE_NARRATION` | Include narration by default | `true` |

## Limitations & Considerations

- **OpenRouter Costs**: Vary by model (Claude 3.5 Sonnet recommended)
- **Generation Time**: 10-20 seconds per trailer depending on complexity
- **Character Limit**: Focuses on top 4 cast members for consistency
- **Duration Range**: 20-60 seconds (optimal 30-45 seconds)
- **LLM Dependency**: Output quality depends on selected model

## Troubleshooting

### "OpenRouter API key not configured"
- Check that your `.env` file exists and contains `OPENROUTER_API_KEY`
- Verify the key is valid at [openrouter.ai](https://openrouter.ai/keys)

### Generation takes too long
- Try a faster model: `google/gemini-2.0-flash-exp:free`
- Reduce trailer duration
- Check OpenRouter status

### Scenes don't maintain character consistency
- Review the `character_appearance_map` in output
- Check `continuity_guide` for physical descriptions
- Ensure you're using the end_frame → start_frame pattern in VEO

### Docker issues
- Ensure ports aren't in use: `lsof -i :8001`
- Check logs: `docker-compose logs -f`
- Rebuild: `docker-compose up --build`

## Future Enhancements

- [ ] Support for multiple trailer variants (teaser, full trailer, TV spot)
- [ ] Automatic music selection suggestions
- [ ] Scene timing optimization based on genre
- [ ] Integration with video editing timelines
- [ ] Multi-language narration support
- [ ] Custom cinematography style presets

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on the repository.

---

**Part of the AI Movie Production Pipeline**
- Movie Generator: [mcp-screenplay](../mcp-screenplay)
- Trailer Generator: [mcp-trailer-generator](.) (this service)
- Orchestrator: Coming soon
