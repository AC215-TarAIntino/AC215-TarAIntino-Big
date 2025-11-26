# Video Generator Service

A FastAPI service that generates AI-powered movie trailers using Google Gemini (Imagen 3 for images, VEO 3.1 for videos) and uploads results to Google Cloud Storage.

## Overview

The Video Generator is the final step in the TarAIntino pipeline. It takes scene breakdowns from the Scene Decomposer and creates:

1. **Character Reference Images**: Generate visual character designs using Imagen 3
2. **Scene Videos**: Create video clips for each scene using VEO 3.1
3. **Final Trailer**: Stitch videos together into a complete trailer
4. **Cloud Upload**: Upload to GCS for streaming to users

## Technology Stack

- **Framework**: FastAPI (Python)
- **Image Generation**: Google Gemini Imagen 3
- **Video Generation**: Google VEO 3.1 (Vertex AI)
- **Cloud Storage**: Google Cloud Storage (GCS)
- **Video Processing**: FFmpeg (optional for stitching)
- **Port**: 8003

## Project Structure

```
video-generator/
├── app.py                      # FastAPI application
├── generate.py                 # Core video generation logic
├── test.py                     # Test utilities
├── output/                     # Local generated assets
│   ├── refs/                   # Character reference images
│   └── scenes/                 # Generated scene videos
├── secrets.json                # Gemini API key
├── gcp-credentials.json        # GCS service account
├── Dockerfile                  # Container definition
└── pyproject.toml              # Python dependencies
```

## How It Works

### 1. Character Reference Generation

**Purpose**: Create consistent visual character designs

**Process**:
```
Scene Breakdown (characters list)
  ↓
Extract unique characters
  ↓
For each character:
  - Build image prompt: "Portrait of [name] - [description]"
  - Call Gemini Imagen 3 API
  - Save to output/refs/{character_name}.png
  - Upload to GCS bucket
```

### 2. Scene Video Generation

**Purpose**: Generate video clips for each trailer scene

**Process**:
```
For each scene:
  1. Build video prompt:
     - Scene description
     - Visual style
     - Camera movement
     - Character references (as conditioning)

  2. Call Google VEO 3.1 API
     - Duration: 3-8 seconds per scene
     - Resolution: 720p or 1080p
     - Frame rate: 24fps

  3. Poll for completion (async)
     - VEO takes 30-120 seconds per scene
     - Check status every 10 seconds

  4. Download video to output/scenes/scene_{n}.mp4

  5. Upload to GCS
```

### 3. Video Assembly

**Purpose**: Combine scenes into final trailer

**Options**:
- **Simple Concatenation**: Stitch videos sequentially with FFmpeg
- **Cloud-Based**: Upload individual scenes and assemble client-side
- **Advanced Editing**: Add transitions, music, effects (optional)

**Process**:
```
output/scenes/scene_1.mp4
output/scenes/scene_2.mp4
...
output/scenes/scene_7.mp4
  ↓
FFmpeg: concat all scenes
  ↓
output/final_trailer.mp4
  ↓
Upload to GCS: gs://tarantaino-output/trailers/{session_id}.mp4
```

### 4. GCS Upload

**Purpose**: Make videos accessible to frontend

**Bucket Structure**:
```
gs://tarantaino-output/
├── video_generator_outputs/
│   ├── refs/
│   │   ├── alex_chen.png
│   │   └── maya_rodriguez.png
│   ├── scenes/
│   │   ├── scene_1.mp4
│   │   ├── scene_2.mp4
│   │   └── ...
│   └── trailers/
│       └── {session_id}.mp4
```

**Access**: Videos are publicly accessible via GCS URLs

## API Endpoints

### `POST /generate/character-references`
Generate character reference images.

### `POST /generate/scene-videos`
Generate video clips for each scene.

### `POST /generate/trailer`
Full pipeline: Generate characters, scenes, and final trailer.

### `GET /health`
Health check endpoint.

## Running Locally

-> See main [README](../README.md) for full setup instructions.

### Prerequisites

You need two credential files:

1. **Gemini API Key** (`secrets.json`)
   - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Format:
     ```json
     {
       "project_api_key": "YOUR_GEMINI_API_KEY"
     }
     ```

2. **GCS Service Account** (`gcp-credentials.json`)
   - Create in [GCP Console](https://console.cloud.google.com/)
   - IAM → Service Accounts → Create Key (JSON)
   - Grant "Storage Object Admin" role

## Environment Variables

```bash
# GCS Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json
GCS_BUCKET_NAME=tarantaino-output
GCS_PREFIX=video_generator_outputs
```

## Key Features

- **Character Consistency**: Reference images ensure characters look the same across scenes
- **High Quality**: VEO 3.1 generates cinematic-quality video
- **Async Processing**: Non-blocking video generation with polling
- **Cloud Storage**: Seamless upload to GCS
- **Error Handling**: Retries and fallbacks for API failures
- **Progress Tracking**: Status updates for long-running jobs

## Notes: Timing & Performance

### Generation Times (Approximate)

- **Character Reference (Imagen 3)**: 3-10 seconds per image
- **Scene Video (VEO 3.1)**: 30-120 seconds per scene
- **Full Trailer (7 scenes)**: 3-10 minutes total

## Costs (Google Cloud Pricing)

- **Imagen 3**: ~$0.02 per image
- **VEO 3.1**: ~$0.50 - $1.00 per video second
- **GCS Storage**: ~$0.02 per GB per month
- **GCS Bandwidth**: ~$0.12 per GB (egress)

**Estimated cost per trailer**: $15-25 for a 35-second trailer with 7 scenes

## Related Documentation

- [Main Project README](../README.md)
- [System Architecture](../hand-ins/system-architecture-diagram.md)
- [Scene Decomposer Documentation](../scene-decomposer/README.md)
- [Frontend Documentation](../frontend/README.md)
