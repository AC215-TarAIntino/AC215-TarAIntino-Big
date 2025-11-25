# Scene Decomposer Service

AI-powered microservice that generates detailed scene-by-scene trailer breakdowns from movie descriptions. Creates production-ready prompts for video generation (VEO 3.1), image generation (DALL-E/Flux), and narration (ElevenLabs).

## Overview

This service takes a complete movie description (from `screenplay-writer` or similar) and generates a detailed trailer breakdown with:

- **Character reference images**: Generates design prompts for up to 4 main characters (white background, visual style-matched)
- **Scene-by-scene structure**: 4-8 scenes, each 4-8 seconds long (8s when using character references)
- **Image generation prompts**: Detailed start/end frame descriptions
- **Video generation prompts**: Comprehensive VEO 3.1 prompts with motion, camera movement, cinematography
- **Character consistency**: Uses VEO 3.1's `referenceImages` parameter for consistent character appearance across any scenes
- **Optional narration**: Script for ElevenLabs voice generation
- **Technical specifications**: Color grading, aspect ratio (16:9 for VEO), sound design notes

## Key Features

- **VEO 3.1 Reference Images**: Pre-generates character design prompts for consistent appearance across ANY scenes (no continuity chains needed!)
- **Character Design System**: Generates detailed prompts for character reference images on white backgrounds, matching movie visual style
- **Self-Contained Prompts**: Every prompt is completely independent with full context - no references to previous scenes
- **Audio Integration**: Sound design naturally woven into video prompts (VEO 3.1 generates audio)
- **Validation Logic**: Ensures VEO 3.1 constraints (8s duration with refs, max 3 refs per scene)
- **Flexible Duration**: Generate 20-60 second trailers
- **Multiple Interfaces**: REST API, Python library, or standalone CLI
- **Docker Ready**: Easy containerization and deployment

## How It Works: VEO 3.1 Reference Images System

**Critical Concept**: Video generation models (VEO 3.1) have NO MEMORY between API calls. Each prompt must be completely self-contained.

### Two-Phase Generation

The service generates trailers in two phases:

**Phase 1: Character Designs**
- Generates detailed design prompts for up to 4 main characters
- Each design specifies:
  - Character name (e.g., "Dr_Elara_Vance")
  - Complete physical description prompt (on white background)
  - Visual style matching movie aesthetic (hyper-realistic, 3D animated, etc.)
  - Brief identifier for use in scene prompts (e.g., "slender woman, late 30s, dark hair")

**Phase 2: Scene Generation**
- Creates 4-8 scenes with full context prompts
- Each scene can reference up to 3 characters via `reference_images` array
- Characters can appear in ANY scenes (not limited to continuous sequences!)

### Character Consistency via Reference Images

**Revolutionary Approach**: VEO 3.1's `referenceImages` parameter maintains character consistency WITHOUT requiring continuous scene chains.

**How it works:**
1. Orchestrator generates character reference images from design prompts (Phase 1)
2. For each scene with characters, passes those character images to VEO 3.1 via `referenceImages`
3. VEO 3.1 maintains character appearance consistency across ANY scenes

**Example:**
```
Phase 1: Generate character designs
  - Dr_Elara_Vance → character_ref_1.png
  - General_Kade → character_ref_2.png

Phase 2: Generate scenes
  Scene 1: Dr. Vance + General Kade (8s, reference_images: ["Dr_Elara_Vance", "General_Kade"])
  Scene 2: Establishing shot (6s, reference_images: [])
  Scene 3: Dr. Vance alone (8s, reference_images: ["Dr_Elara_Vance"])
  Scene 4: General Kade (8s, reference_images: ["General_Kade"])

✅ Characters can appear in ANY scenes - consistency maintained via reference images!
```

### VEO 3.1 Requirements with Reference Images

When using reference images:
- **Duration**: Must be exactly 8 seconds
- **Max References**: Up to 3 character images per scene
- **Aspect Ratio**: 16:9 (VEO 3.1 limitation)
- **Parameter**: `personGeneration: "allow_adult"` required

### Self-Contained Prompts

Every prompt includes COMPLETE context:

❌ **Bad** (references previous):
```
"The camera has risen higher, revealing more of the facility..."
```

✅ **Good** (self-contained):
```
"Aerial view from 150 meters altitude of Project Cacophony research facility,
a 300-meter tall brutalist grey structure rising from bioluminescent jungle on
the moon Veridia..."
```

### Audio Integration

Audio is integrated naturally into `video_prompt` (not separate):

```
"...Dr. Vance's fingers trace patterns in the glowing holographic display while
the lab equipment emits a low 60Hz electronic hum. The Chrysalids begin pulsing,
producing harmonic crystalline tones building from 440Hz to 880Hz. She whispers:
'It's not a weapon... it's a language.' The tones crescendo, mixing with her
controlled breathing."
```

## Architecture

Part of a larger AI movie production pipeline:

```
screenplay-writer → movie.json
    ↓
scene-decomposer → trailer_scenes.json
    ↓
video-generator → actual video (VEO 3.1 API calls)
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

1. **Navigate to service directory**
```bash
cd scene-decomposer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -e .
# Or for development with testing tools:
pip install -e ".[dev]"
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
  --movie-file ../screenplay-writer/outputs/test_scifi.json \
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
    "character_designs": [
      {
        "character_name": "Dr_Elara_Vance",
        "image_generation_prompt": "A slender woman in her late 30s with long dark chestnut hair tied in a messy bun and warm hazel eyes, standing on a pure white background. She has an intelligent, focused expression with slight worry lines on her forehead. Wearing a fitted grey lab coat over a simple black shirt with practical dark pants. Hyper-realistic style with precise anatomical detail. Standing facing camera in neutral pose, 3/4 body shot. Soft, even lighting with no harsh shadows...",
        "brief_identifier": "slender woman, late 30s, dark hair",
        "visual_style": "hyper-realistic"
      },
      {
        "character_name": "General_Valerius_Kade",
        "image_generation_prompt": "An imposing man standing 6'2\" with silver-grey hair in military cut, standing on a pure white background. He has steely grey eyes and a commanding presence with military bearing. Wearing dark military-style tactical uniform with insignia. Hyper-realistic style. Standing facing camera, neutral expression, full body shot. Soft, even lighting...",
        "brief_identifier": "imposing man, grey hair, military bearing",
        "visual_style": "hyper-realistic"
      }
    ],
    "scenes": [
      {
        "scene_number": 1,
        "duration_seconds": 8,
        "scene_type": "character_introduction",
        "start_frame_prompt": "Dr. Vance (slender woman, late 30s, dark hair) and General Kade (imposing man, grey hair, military bearing) stand at the entrance of Project Cacophony facility. SELF-CONTAINED 4-5 sentence description with full context...",
        "end_frame_prompt": "SELF-CONTAINED 4-5 sentence description...",
        "video_prompt": "The camera executes a dolly forward toward Dr. Vance (slender woman, late 30s, dark hair) and General Kade (imposing man, grey hair, military bearing). SELF-CONTAINED 6-8 sentence prompt with camera movement AND audio naturally integrated...",
        "reference_images": ["Dr_Elara_Vance", "General_Valerius_Kade"],
        "characters_present": ["Dr. Elara Vance", "General Valerius Kade"],
        "continuity_note": "Optional metadata note"
      },
      {
        "scene_number": 2,
        "duration_seconds": 6,
        "scene_type": "establishing",
        "start_frame_prompt": "Wide aerial view of the facility. SELF-CONTAINED description, no characters...",
        "end_frame_prompt": "SELF-CONTAINED description...",
        "video_prompt": "SELF-CONTAINED with audio...",
        "reference_images": [],
        "characters_present": [],
        "continuity_note": "Establishing shot"
      }
    ],
    "narration_script": "Compelling narration text...",
    "continuity_guide": "Brief visual consistency guide...",
    "technical_specs": {
      "color_grading": "Desaturated with teal shadows...",
      "aspect_ratio": "16:9",
      "visual_style": "...",
      "sound_design_notes": "..."
    },
    "character_appearance_map": {
      "Dr. Elara Vance": [1],
      "General Valerius Kade": [1]
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

### Character Designs (Phase 1)

Each character design includes:

1. **character_name**: Formatted as "FirstName_LastName" for use as filename
2. **image_generation_prompt**: Complete 6-8 sentence prompt for generating reference image
   - Must include "standing on a pure white background"
   - Specifies visual style (hyper-realistic, 3D animated, etc.)
   - Full physical description (height, build, age, features, clothing)
   - Neutral pose, even lighting
3. **brief_identifier**: 3-5 word shorthand for use in scene prompts
4. **visual_style**: Matches movie aesthetic (determined by LLM from movie data)

### Scene Structure (Phase 2)

Each scene includes three critical prompts plus reference metadata:

1. **start_frame_prompt**: Detailed description for generating the opening image
   - Characters identified as "Name (brief_identifier)"
   - Lighting and color palette
   - Composition and camera angle
   - Setting details

2. **end_frame_prompt**: Detailed description for the closing image
   - Shows progression from start frame
   - Complete self-contained description

3. **video_prompt**: Comprehensive instructions for VEO 3.1
   - Characters identified as "Name (brief_identifier)"
   - Explicit camera movement (dolly, crane, handheld, etc.)
   - Subject motion description
   - Pacing and timing
   - Cinematography style
   - Specific events that occur
   - Atmosphere and mood
   - Audio design naturally integrated

4. **reference_images**: List of character_names to use as VEO 3.1 reference images (max 3)

### Character Consistency

The system uses VEO 3.1's `referenceImages` parameter for consistency:

```
✅ Characters can appear in ANY scenes - reference images maintain consistency!

Example:
  Scene 1: Dr. Vance + General Kade (reference_images: ["Dr_Elara_Vance", "General_Valerius_Kade"])
  Scene 2: Establishing shot (reference_images: [])
  Scene 3: Dr. Vance alone (reference_images: ["Dr_Elara_Vance"])

All scenes maintain character consistency via reference images!
```

## Integration with Larger Systems

### Recommended Architecture

```
┌─────────────────┐
│ screenplay-     │ → Generates movie descriptions
│ writer          │
└────────┬────────┘
         │
         ↓ movie.json
┌─────────────────────┐
│ scene-decomposer    │ → Generates scene breakdown
└────────┬────────────┘
         │
         ↓ trailer_scenes.json
┌─────────────────────┐
│ video-generator     │ → Calls VEO, DALL-E, ElevenLabs APIs
│                     │ → Stitches video
└────────┬────────────┘
         │
         ↓
    final_trailer.mp4
```

### Example Integration

```python
# In your orchestrator service
import requests
from typing import Dict

# 1. Generate movie description
movie_response = requests.post(
    "http://screenplay-writer:8080/generate-movie",
    json={"movie_names": ["Inception", "The Matrix"]}
)
movie = movie_response.json()["movie"]

# 2. Generate trailer breakdown
trailer_response = requests.post(
    "http://scene-decomposer:8001/generate-trailer",
    json={"movie": movie, "target_duration": 35}
)
trailer = trailer_response.json()["trailer"]

# 3. PHASE 1: Generate character reference images
character_ref_images: Dict[str, str] = {}

for design in trailer["character_designs"]:
    char_name = design["character_name"]
    print(f"Generating reference image for {char_name}...")

    # Generate character image using DALL-E/Flux
    ref_img = generate_image(
        prompt=design["image_generation_prompt"],
        # Important: This creates the character on white background
    )

    # Store for use in scenes
    character_ref_images[char_name] = ref_img
    # Optionally save: ref_img.save(f"refs/{char_name}.png")

print(f"✅ Generated {len(character_ref_images)} character reference images")

# 4. PHASE 2: Generate scene videos with VEO 3.1
for scene in trailer["scenes"]:
    print(f"\nGenerating Scene {scene['scene_number']}: {scene['scene_type']}")

    # Generate start and end frames
    start_img = generate_image(scene["start_frame_prompt"])
    end_img = generate_image(scene["end_frame_prompt"])

    # Prepare reference images for this scene
    scene_refs = []
    if scene["reference_images"]:
        for char_name in scene["reference_images"]:
            scene_refs.append(character_ref_images[char_name])
        print(f"  Using {len(scene_refs)} character reference(s)")

    # Generate video with VEO 3.1
    # video_prompt already includes audio design
    veo_params = {
        "prompt": scene["video_prompt"],
        "image": start_img,  # Start frame
        "lastFrame": end_img,  # End frame
        "duration": scene["duration_seconds"],
        "aspectRatio": "16:9",  # Required with reference images
    }

    # Add reference images if present (VEO 3.1 feature)
    if scene_refs:
        veo_params["referenceImages"] = scene_refs
        veo_params["personGeneration"] = "allow_adult"  # Required with refs

    video = call_veo_api(**veo_params)

    # Collect videos for final stitching...

# 5. Stitch videos together, add narration, etc.
```

## Project Structure

```
scene-decomposer/
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
├── pyproject.toml                 # Python dependencies and config
├── Dockerfile                     # Docker container config
├── docker-compose.yml             # Docker Compose config
├── .env.example                   # Environment template
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
- Ensure you're generating character reference images from `character_designs`
- Verify you're passing those images to VEO 3.1 via `referenceImages` parameter
- Check that `personGeneration: "allow_adult"` is set when using reference images
- Review the `character_appearance_map` to see which scenes include which characters

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
- Movie Generator: [screenplay-writer](../screenplay-writer)
- Trailer Generator: [scene-decomposer](.) (this service)
- Video Generator: [video-generator](../video-generator)
